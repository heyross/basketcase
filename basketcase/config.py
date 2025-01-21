"""Configuration settings for the basketcase package."""
import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory for storing SQLite database and other files
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Logs directory
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Database
DATABASE_PATH = DATA_DIR / "basketcase.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Kroger API
KROGER_BASE_URL = "https://api.kroger.com/v1"
KROGER_CLIENT_ID = os.getenv("KROGER_CLIENT_ID")
KROGER_CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET")

# Error logging
ERROR_LOG_PATH = LOGS_DIR / "error.log"

# Price update settings
PRICE_UPDATE_INTERVAL = 7  # days
MAX_PRODUCTS_PER_REQUEST = 50  # Kroger API limit

# Basket settings
MAX_BASKET_ITEMS = 50
