import logging.config
import os
import platform

if platform.system() == 'Windows':
    LOG_FILE = os.path.join(os.getenv('LOCALAPPDATA'), 'SCORHE', 'Logs', 'acquisition.log')
    if not os.path.exists(LOG_FILE.rstrip('acquisition.log')):
        os.makedirs(LOG_FILE.rstrip('acquisition.log'))
elif platform.system() == 'Linux':
    LOG_FILE = '/dev/null'
else:
    raise OSError('Unsupported OS: {}'.format(platform.system()))

LOGGING = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s@%(funcName)s:%(lineno)d]: %(message)s'
        },
        'nodate': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s@%(funcName)s:%(lineno)d]: %(message)s',
            'datefmt': '%H:%M:%S'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'filename': LOG_FILE,
            'maxBytes': 1024*1024,  # 1 MB log
            'backupCount': 10
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'acquisition': {}
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    }
}

logging.config.dictConfig(LOGGING)
