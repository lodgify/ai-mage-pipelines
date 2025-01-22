import sys

from loguru import logger

logger.remove(0)
# removing time because Mage is showing it in the logs
logger.add(sys.stderr, format="{level} | {message}")
