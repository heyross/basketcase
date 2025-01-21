"""Basketcase - A local grocery price tracking application."""
from pathlib import Path
from dotenv import load_dotenv

__version__ = "0.1.0"

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)
