from slowapi import Limiter
from slowapi.util import get_remote_address

# Define the limiter here, once
limiter = Limiter(key_func=get_remote_address)
