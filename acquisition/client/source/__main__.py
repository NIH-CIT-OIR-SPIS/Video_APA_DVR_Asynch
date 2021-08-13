import os
import logging.config
import platform
import sys

if platform.system() == 'Windows':
    LOG_FILE = os.path.join(os.getenv('LOCALAPPDATA'), 'SCORHE', 'Logs', 'acquisition.log')
    if not os.path.exists(LOG_FILE.rstrip('acquisition.log')):
        os.makedirs(LOG_FILE.rstrip('acquisition.log'))
elif platform.system() == 'Linux':
    LOG_FILE = '/home/pi/scorhe.log'
else:
    raise OSError('Unsupported OS: {}'.format(platform.system()))

LOGGING = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'
        },
        'nodate': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
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

from client import main, NAME, VERSION

print('{} v{}'.format(NAME, VERSION))
argv = sys.argv[1:]
try:
    os.chdir(argv[0])
except (IndexError, FileNotFoundError):
    os.chdir('/home/pi/scripts')
main()
