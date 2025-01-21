"""Test cases for Kroger API client."""
from datetime import datetime, timedelta

import pytest
from requests.exceptions import RequestException

from basketcase.api import KrogerAPI


def test_api_initialization():
    """Test API client initialization."""
    api = KrogerAPI()
    assert api.token is None
    assert api.token_expiry is None


def test_token_management(mock_kroger_api):
    """Test token acquisition and caching."""
    api = KrogerAPI()
    
    # First token request
    token = api.get_token()
    assert token == "mock_token"
    assert api.token == "mock_token"
    assert api.token_expiry is not None
    
    # Token should be cached
    token2 = api.get_token()
    assert token2 == token
    
    # Expired token should be refreshed
    api.token_expiry = datetime.now() - timedelta(hours=1)
    token3 = api.get_token()
    assert token3 == "mock_token"  # New token from mock


def test_find_stores(mock_kroger_api):
    """Test store location search."""
    api = KrogerAPI()
    stores = api.find_stores("12345")
    assert isinstance(stores, list)


def test_search_products(mock_kroger_api):
    """Test product search."""
    api = KrogerAPI()
    products = api.search_products("milk", "store123")
    assert isinstance(products, list)


def test_get_product_prices(mock_kroger_api):
    """Test getting product prices."""
    api = KrogerAPI()
    prices = api.get_product_prices(["prod123"], "store123")
    assert isinstance(prices, dict)
