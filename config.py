"""Configuration settings for the Basketcase application."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Database
DATABASE_PATH = BASE_DIR / "data" / "basketcase.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Kroger API
KROGER_CLIENT_ID = os.getenv("client_id")
KROGER_BASE_URL = "https://api.kroger.com/v1"

# Application settings
MAX_ITEMS_PER_BASKET = 50
DEFAULT_STORE_RADIUS = 10  # miles
MAX_STORES_TO_TRACK = 5
PRICE_UPDATE_INTERVAL = 7  # days

# API Rate Limits
LOCATION_API_DAILY_LIMIT = 1600
PRODUCT_API_DAILY_LIMIT = 10000

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "basketcase.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Create necessary directories
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
