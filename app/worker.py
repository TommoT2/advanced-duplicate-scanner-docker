"""
Background worker for heavy scanning tasks
"""

import asyncio
import signal
import sys
from pathlib import Path

import structlog
from celery import Celery

from app.core.config import settings

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "duplicate_scanner_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.worker']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

@celery_app.task(bind=True)
def scan_files_task(self, scan_config):
    """Background task for scanning files"""
    logger.info("Starting file scan task", config=scan_config)
    
    try:
        # This would be the actual scanning logic
        # For now, just simulate some work
        import time
        
        paths = scan_config.get('paths', [])
        total_files = 0
        
        for path_str in paths:
            path = Path(path_str)
            if path.exists() and path.is_dir():
                files = list(path.rglob('*'))
                total_files += len([f for f in files if f.is_file()])
        
        # Simulate processing
        for i in range(total_files):
            time.sleep(0.01)  # Simulate work
            
            # Update task progress
            self.update_state(
                state='PROGRESS',
                meta={'current': i + 1, 'total': total_files}
            )
        
        result = {
            'files_processed': total_files,
            'duplicates_found': total_files // 10,  # Mock some duplicates
            'space_saved': total_files * 1024 * 1024  # Mock space saved
        }
        
        logger.info("File scan task completed", result=result)
        return result
        
    except Exception as e:
        logger.error("File scan task failed", error=str(e))
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal", signal=signum)
    sys.exit(0)

def main():
    """Main worker entry point"""
    logger.info("Starting duplicate scanner worker")
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start Celery worker
        celery_app.start([
            'worker',
            '--loglevel=info',
            '--concurrency=4',
            '--pool=prefork'
        ])
    except Exception as e:
        logger.error("Worker startup failed", error=str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()