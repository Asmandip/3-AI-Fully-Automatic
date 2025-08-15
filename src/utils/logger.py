# src/utils/logger.py
import logging
import os
from logging.config import dictConfig

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
            'filename': os.getenv('LOG_FILE', 'logs/trading.log'),
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
