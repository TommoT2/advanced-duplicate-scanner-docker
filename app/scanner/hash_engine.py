"""
Advanced hashing engine with chunked processing and multiple algorithms
"""

import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Callable
import aiofiles
try:
    import blake3
except ImportError:
    blake3 = None
try:
    import xxhash
except ImportError:
    xxhash = None
import structlog

logger = structlog.get_logger(__name__)

class HashEngine:
    """High-performance file hashing with multiple algorithms"""
    
    def __init__(self, chunk_size: int = 8 * 1024 * 1024, workers: int = 4):
        self.chunk_size = chunk_size
        self.executor = ThreadPoolExecutor(max_workers=workers)
        logger.info("Hash engine initialized", chunk_size=chunk_size, workers=workers)
        
    async def hash_file(
        self, 
        file_path: Union[str, Path],
        algorithms: List[str] = ["blake3", "xxhash64"],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, str]:
        """
        Hash a file using specified algorithms with chunked processing
        
        Args:
            file_path: Path to file to hash
            algorithms: List of hash algorithms to use
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary of algorithm -> hash mappings
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = file_path.stat().st_size
        
        # Initialize hashers
        hashers = {}
        if "blake3" in algorithms and blake3:
            hashers["blake3"] = blake3.blake3()
        if "xxhash64" in algorithms and xxhash:
            hashers["xxhash64"] = xxhash.xxh64()
        if "sha256" in algorithms:
            hashers["sha256"] = hashlib.sha256()
        if "md5" in algorithms:
            hashers["md5"] = hashlib.md5()
        
        # Fallback to SHA-256 if no other hashers available
        if not hashers:
            hashers["sha256"] = hashlib.sha256()
            logger.warning("No preferred hash libraries available, using SHA-256")
        
        bytes_processed = 0
        
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                while True:
                    chunk = await f.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    # Process chunk in thread pool to avoid blocking
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        self._update_hashers,
                        hashers,
                        chunk
                    )
                    
                    bytes_processed += len(chunk)
                    
                    # Call progress callback if provided
                    if progress_callback:
                        progress = bytes_processed / file_size if file_size > 0 else 1.0
                        try:
                            await progress_callback(progress, bytes_processed, file_size)
                        except Exception as e:
                            logger.warning("Progress callback failed", error=str(e))
        
        except Exception as e:
            logger.error("Error hashing file", file_path=str(file_path), error=str(e))
            raise
        
        # Get final hash values
        results = {}
        for algo, hasher in hashers.items():
            try:
                if algo == "blake3" and blake3:
                    results[algo] = hasher.hexdigest()
                elif algo == "xxhash64" and xxhash:
                    results[algo] = hasher.hexdigest()
                else:
                    results[algo] = hasher.hexdigest()
            except Exception as e:
                logger.warning("Failed to get hash digest", algorithm=algo, error=str(e))
        
        logger.debug(
            "File hashed successfully",
            file_path=str(file_path),
            file_size=file_size,
            algorithms=list(results.keys())
        )
        
        return results
    
    def _update_hashers(self, hashers: Dict, chunk: bytes) -> None:
        """Update all hashers with chunk data (runs in thread pool)"""
        for hasher in hashers.values():
            try:
                hasher.update(chunk)
            except Exception as e:
                logger.warning("Failed to update hasher", error=str(e))
    
    async def quick_hash(self, file_path: Union[str, Path]) -> str:
        """
        Quick hash using xxHash64 or SHA-256 for fast pre-filtering
        
        Args:
            file_path: Path to file to hash
            
        Returns:
            Hash hex digest
        """
        file_path = Path(file_path)
        
        # Use xxHash64 if available, otherwise SHA-256
        if xxhash:
            hasher = xxhash.xxh64()
        else:
            hasher = hashlib.sha256()
        
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                while True:
                    chunk = await f.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        hasher.update,
                        chunk
                    )
        except Exception as e:
            logger.error("Error in quick hash", file_path=str(file_path), error=str(e))
            raise
        
        return hasher.hexdigest()
    
    async def shutdown(self):
        """Shutdown the hash engine and cleanup resources"""
        self.executor.shutdown(wait=True)
        logger.info("Hash engine shutdown complete")