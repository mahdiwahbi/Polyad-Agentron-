import logging
import json
from datetime import datetime
from typing import Dict
import os

class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON logs"""
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process': record.process,
            'thread': record.threadName
        }
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        return json.dumps(log_entry)

def setup_logging(config: Dict) -> None:
    """Configure logging system"""
    log_level = config.get('logging', {}).get('level', 'INFO').upper()
    log_dir = config.get('logging', {}).get('directory', 'logs')
    
    # Create log directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    console_handler.setLevel(log_level)
    
    # File handler
    file_handler = logging.FileHandler(
        os.path.join(log_dir, 'polyad.log'),
        encoding='utf-8'
    )
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(log_level)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get configured logger"""
    return logging.getLogger(name)
