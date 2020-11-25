from .base import *

DEBUG = False
if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, '/static/')
