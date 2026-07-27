from decouple import config

env_state = config("ENVIRONMENT", default="development").lower()

if env_state == "production":
    from .production import *
else:
    from .development import *
