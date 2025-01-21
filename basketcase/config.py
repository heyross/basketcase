"""Configuration settings for the basketcase package."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if not KROGER_CLIENT_ID or not KROGER_CLIENT_SECRET:
    raise ValueError(
        "Missing Kroger API credentials. Please set KROGER_CLIENT_ID and KROGER_CLIENT_SECRET environment variables."
    )
