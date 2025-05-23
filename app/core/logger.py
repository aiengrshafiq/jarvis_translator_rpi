# logger.py
from loguru import logger
import sys
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(f"{LOG_DIR}/assistant.log", rotation="500 KB", level="DEBUG", backtrace=True, diagnose=True)

def get_logger(name: str):
    return logger.bind(module=name)