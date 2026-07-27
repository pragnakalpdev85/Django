from .base import *
from decouple import config

DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = ["*"]

# In development, you might want to use a local sqlite db instead if postgres isn't up
# But we will stick to the default db config provided by base.py for now
