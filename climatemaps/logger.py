import logging


logger = logging.getLogger('climatemaps')
logger.setLevel(logging.DEBUG)

handlers = []

# console handlers
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
handlers.append(console)

# file handlers
error_file = logging.FileHandler('error.log')
error_file.setLevel(logging.ERROR)
handlers.append(error_file)
info_file = logging.FileHandler('info.log')
info_file.setLevel(logging.INFO)
handlers.append(info_file)
debug_file = logging.FileHandler('debug.log')
debug_file.setLevel(logging.DEBUG)
handlers.append(debug_file)

format = "[%(asctime)s] %(levelname)s [%(funcName)s() (%(lineno)s)]: %(message)s"
date_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(format, date_fmt)

for handler in handlers:
    handler.setFormatter(formatter)

for handler in handlers:
    logger.addHandler(handler)
