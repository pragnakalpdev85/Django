from .base import *
from decouple import config

DEBUG = False

# Usually you would specify the allowed hosts for production in the environment
allowed_hosts_str = config("ALLOWED_HOSTS", default="")
if allowed_hosts_str:
    ALLOWED_HOSTS = allowed_hosts_str.split(",")
else:
    ALLOWED_HOSTS = []
