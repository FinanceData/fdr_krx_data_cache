import sys
import logging
from main import collect_historical_yearly_indices
from krx_auth import login

# Set up logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

if login():
    print("Login successful")
    collect_historical_yearly_indices()
    print("Collection done")
else:
    print("Login failed")
