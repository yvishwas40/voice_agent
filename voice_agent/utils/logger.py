import logging
import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""
    
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, Fore.WHITE)
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"

def setup_logger(name="VoiceAgent", level=logging.INFO):
    """Sets up a logger with colored console output"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console Handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter("%(asctime)s - [%(levelname)s] - %(message)s", datefmt="%H:%M:%S"))
    
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

# Global logger instance
logger = setup_logger()
