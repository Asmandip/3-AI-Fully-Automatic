# src/utils/logger.py
import logging
import os
from logging.config import dictConfig

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        }
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'default'},
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'trading.log'),
            'when': 'midnight',
            'backupCount': 7,
            'formatter': 'default'
        }
    },
    'root': {'level': os.getenv('LOG_LEVEL', 'INFO'), 'handlers': ['console', 'file']},
}

dictConfig(LOG_CONFIG)

def get_logger(name):
    return logging.getLogger(name)