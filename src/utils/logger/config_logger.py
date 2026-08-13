from logging import DEBUG

LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'utils.logger.json_logger.JSONLogFormatter',
        },
    },
    'handlers': {
# Используем AsyncLogDispatcher для асинхронного вывода потока.
        'json': {
            'formatter': 'json',
            'class': 'asynclog.AsyncLogDispatcher',
            'func': 'utils.logger.json_logger.write_log',
        },
    },
    'loggers': {
        'work-selenium': {
            'handlers': ['json'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },

        'shedular.proxy': {
            'handlers': ['json'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'handlers/middlewares': {
            'handlers': ['json'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'service.number': {
            'handlers': ['json'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,

        },'restore_service': {
            'handlers': ['json'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'work-selenium': {
            'handlers': ['json'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'uvicorn': {
            'handlers': ['json'],
            'level': 'INFO',
            'propagate': False,
        },
      # Не даем стандартному логгеру fastapi работать по пустякам и замедлять работу сервиса
        'uvicorn.access': {
            'handlers': ['json'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
