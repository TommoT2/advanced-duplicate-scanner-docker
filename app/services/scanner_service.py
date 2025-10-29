"""
Main scanner service for duplicate detection
"""

import asyncio
from typing import List, Dict, Optional, Any
from pathlib import Path
import structlog

from app.core.config import settings
from app.scanner.hash_engine import HashEngine
from app.services.websocket_manager import WebSocketManager

logger = structlog.get_logger(__name__)

class ScannerService:
    """Main scanner service coordinating all scanning operations"""
    
    def __init__(self, websocket_manager: Optional[WebSocketManager] = None):
        self.websocket_manager = websocket_manager
        self.hash_engine: Optional[HashEngine] = None
        self.active_scans: Dict[int, Dict[str, Any]] = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the scanner service"""
        try:
            # Initialize hash engine
            self.hash_engine = HashEngine(
                chunk_size=settings.SCANNER_CHUNK_SIZE,
                workers=settings.SCANNER_WORKERS
            )
            
            # Test basic functionality
            await self._test_initialization()
            
            self.is_initialized = True
            logger.info("Scanner service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize scanner service", error=str(e))
            raise
    
    async def _test_initialization(self):
        """Test that all components are working"""
        # Test data path access
        data_path = Path(settings.DATA_PATH)
        if not data_path.exists():
            logger.warning("Data path does not exist, will be created if needed", path=str(data_path))
        
        # Test hash engine with a small dummy file if possible
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                tf.write(b"test data for initialization")
                tf.flush()
                
                result = await self.hash_engine.quick_hash(tf.name)
                logger.info("Hash engine test successful", test_hash=result[:16] + "...")
                
                # Cleanup
                Path(tf.name).unlink(missing_ok=True)
                
        except Exception as e:
            logger.warning("Hash engine test failed, but continuing", error=str(e))
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current scanner status"""
        return {
            "initialized": self.is_initialized,
            "active_scans": len(self.active_scans),
            "scan_sessions": list(self.active_scans.keys()),
            "workers_configured": settings.SCANNER_WORKERS,
            "chunk_size": settings.SCANNER_CHUNK_SIZE
        }
    
    async def start_scan(self, scan_config: Dict[str, Any]) -> int:
        """Start a new duplicate scan"""
        if not self.is_initialized:
            raise RuntimeError("Scanner service not initialized")
        
        scan_id = len(self.active_scans) + 1
        
        # Create scan session record
        scan_session = {
            "id": scan_id,
            "status": "starting",
            "config": scan_config,
            "progress": {
                "files_found": 0,
                "files_processed": 0,
                "duplicates_found": 0,
                "current_file": None
            },
            "start_time": asyncio.get_event_loop().time()
        }
        
        self.active_scans[scan_id] = scan_session
        
        # Start scanning in background
        asyncio.create_task(self._run_scan(scan_id))
        
        logger.info("Scan started", scan_id=scan_id, config=scan_config)
        return scan_id
    
    async def _run_scan(self, scan_id: int):
        """Run the actual scanning process"""
        scan_session = self.active_scans[scan_id]
        
        try:
            scan_session["status"] = "running"
            
            # Notify WebSocket clients
            if self.websocket_manager:
                await self.websocket_manager.broadcast({
                    "type": "scan_started",
                    "scan_id": scan_id,
                    "status": "running"
                })
            
            # Get paths to scan
            paths = scan_session["config"].get("paths", [])
            algorithms = scan_session["config"].get("algorithms", ["blake3"])
            
            # Discover files
            all_files = []
            for path_str in paths:
                path = Path(path_str)
                if path.exists():
                    if path.is_file():
                        all_files.append(path)
                    elif path.is_dir():
                        # Recursively find all files
                        all_files.extend(self._discover_files(path))
            
            scan_session["progress"]["files_found"] = len(all_files)
            
            # Process files
            processed = 0
            file_hashes = {}
            
            for file_path in all_files:
                try:
                    scan_session["progress"]["current_file"] = str(file_path)
                    
                    # Hash the file
                    hashes = await self.hash_engine.hash_file(
                        file_path, 
                        algorithms=algorithms,
                        progress_callback=self._create_progress_callback(scan_id)
                    )
                    
                    # Track by primary hash
                    primary_hash = hashes.get("blake3", hashes.get("xxhash64"))
                    if primary_hash:
                        if primary_hash not in file_hashes:
                            file_hashes[primary_hash] = []
                        file_hashes[primary_hash].append({
                            "path": str(file_path),
                            "size": file_path.stat().st_size,
                            "hashes": hashes
                        })
                    
                    processed += 1
                    scan_session["progress"]["files_processed"] = processed
                    
                    # Broadcast progress
                    if self.websocket_manager and processed % 10 == 0:
                        await self._broadcast_progress(scan_id)
                    
                except Exception as e:
                    logger.warning("Failed to process file", file=str(file_path), error=str(e))
                    continue
            
            # Find duplicates
            duplicates = {k: v for k, v in file_hashes.items() if len(v) > 1}
            scan_session["progress"]["duplicates_found"] = len(duplicates)
            scan_session["duplicates"] = duplicates
            
            # Complete scan
            scan_session["status"] = "completed"
            scan_session["end_time"] = asyncio.get_event_loop().time()
            
            # Final broadcast
            if self.websocket_manager:
                await self.websocket_manager.broadcast({
                    "type": "scan_completed",
                    "scan_id": scan_id,
                    "duplicates_found": len(duplicates),
                    "files_processed": processed
                })
            
            logger.info(
                "Scan completed", 
                scan_id=scan_id, 
                files_processed=processed,
                duplicates_found=len(duplicates)
            )
            
        except Exception as e:
            scan_session["status"] = "failed"
            scan_session["error"] = str(e)
            logger.error("Scan failed", scan_id=scan_id, error=str(e))
            
            if self.websocket_manager:
                await self.websocket_manager.broadcast({
                    "type": "scan_failed",
                    "scan_id": scan_id,
                    "error": str(e)
                })
    
    def _discover_files(self, path: Path) -> List[Path]:
        """Recursively discover all files in a directory"""
        files = []
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    # Skip hidden files and system files
                    if not item.name.startswith('.') and item.stat().st_size > 0:
                        files.append(item)
        except (PermissionError, OSError) as e:
            logger.warning("Cannot access path", path=str(path), error=str(e))
        
        return files
    
    def _create_progress_callback(self, scan_id: int):
        """Create a progress callback for file processing"""
        async def progress_callback(progress: float, bytes_processed: int, total_bytes: int):
            # This could update more granular progress if needed
            pass
        return progress_callback
    
    async def _broadcast_progress(self, scan_id: int):
        """Broadcast scan progress to WebSocket clients"""
        if not self.websocket_manager:
            return
            
        scan_session = self.active_scans.get(scan_id)
        if not scan_session:
            return
        
        await self.websocket_manager.broadcast({
            "type": "scan_progress",
            "scan_id": scan_id,
            "progress": scan_session["progress"]
        })
    
    async def get_scan_status(self, scan_id: int) -> Optional[Dict[str, Any]]:
        """Get status of a specific scan"""
        return self.active_scans.get(scan_id)
    
    async def cancel_scan(self, scan_id: int) -> bool:
        """Cancel an active scan"""
        scan_session = self.active_scans.get(scan_id)
        if not scan_session:
            return False
        
        scan_session["status"] = "cancelled"
        logger.info("Scan cancelled", scan_id=scan_id)
        return True
    
    async def shutdown(self):
        """Shutdown the scanner service"""
        logger.info("Shutting down scanner service")
        
        # Cancel all active scans
        for scan_id in list(self.active_scans.keys()):
            await self.cancel_scan(scan_id)
        
        # Shutdown hash engine
        if self.hash_engine:
            await self.hash_engine.shutdown()
        
        self.is_initialized = False
        logger.info("Scanner service shutdown complete")