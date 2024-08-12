import os

from dotenv import load_dotenv

load_dotenv()


class Config:
	DEBUG = os.getenv('DEBUG')
	# Don't recall if i need this or use it. TODO: Review later
	DIRECTORY_TO_WATCH = os.getenv('DIRECTORY_TO_WATCH')

	# PostgreSQL configurations
	POSTGRES_USER = os.getenv('POSTGRES_USER')
	POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
	POSTGRES_DB = os.getenv('POSTGRES_DB')
	POSTGRES_HOST = os.getenv('POSTGRES_HOST')
	POSTGRES_PORT = os.getenv('POSTGRES_PORT')
# LOGGING = {
# 	'version': 1,
# 	'disable_existing_loggers': False,
# 	'formatters': {
# 		'default': {
# 			'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
# 		},
# 		'json': {
# 			'()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
# 			'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
# 		},
# 	},
# 	'handlers': {
# 		'file': {
# 			'level': 'INFO',
# 			'class': 'logging.FileHandler',
# 			'filename': 'app.log',
# 			'formatter': 'json',
# 		},
# 		# 'elastic': {
# 		# 	'level': 'INFO',
# 		# 	'class': 'elasticapm.handlers.LoggingHandler',
# 		# 	'formatter': 'json',
# 		# },
# 	},
# 	'root': {
# 		'level': 'INFO',
# 		'handlers': ['file', 'elastic'],
# 	},
# }
