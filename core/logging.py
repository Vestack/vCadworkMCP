"""
Simplified logging configuration
"""
import logging
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logging(name: str = "vCadworkMCP", level: int = logging.INFO) -> None:
    """Setup basic logging configuration"""
    global _logger
    
    # Configure basic logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    _logger = logging.getLogger(name)

def get_logger() -> logging.Logger:
    """Get the configured logger instance"""
    global _logger
    if _logger is None:
        setup_logging()
    # _logger is guaranteed to be non-None after setup_logging()
    assert _logger is not None
    return _logger

def log_info(message: str) -> None:
    """Log info message"""
    get_logger().info(message)

def log_error(message: str) -> None:
    """Log error message"""
    get_logger().error(message)

def log_warning(message: str) -> None:
    """Log warning message"""
    get_logger().warning(message)
