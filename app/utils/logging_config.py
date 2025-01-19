import logging
from pathlib import Path
import os
from datetime import datetime

def setup_logging():
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create a log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"bondalloc_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to console
        ]
    )
    
    # Create loggers for different components
    loggers = {
        'optimization': logging.getLogger('optimization'),
        'data': logging.getLogger('data'),
        'ui': logging.getLogger('ui')
    }
    
    for logger in loggers.values():
        logger.setLevel(logging.INFO)
    
    return loggers
