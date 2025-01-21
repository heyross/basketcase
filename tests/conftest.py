"""Test fixtures and configuration."""
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Add the parent directory to Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from basketcase.models import Base, Store, Category, Product, Basket, BasketItem, PriceHistory, InflationIndex


@pytest.fixture(autouse=True)
def clean_all_tables(db_session):
    """Clean all tables before and after each test."""
    tables = [InflationIndex, PriceHistory, BasketItem, Basket, Product, Category, Store]
    for table in tables:
        db_session.query(table).delete()
    db_session.commit()
    yield
    for table in tables:
        db_session.query(table).delete()
    db_session.commit()


@pytest.fixture
def test_time():
    """Fixed test time to use instead of datetime.now()."""
    return datetime(2025, 1, 20, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def temp_db_path():
    """Create a temporary database file."""
    _, path = tempfile.mkstemp(suffix='.db')
    yield path
    try:
        os.close(_)  # Close the file descriptor
    except OSError:
        pass
    try:
        os.unlink(path)  # Remove the file
    except OSError:
        pass


@pytest.fixture
def test_engine(temp_db_path):
    """Create a test database engine."""
    engine = create_engine(f"sqlite:///{temp_db_path}", echo=False)
    
    # Create tables with indexes
    Base.metadata.create_all(engine)
    
    # Add indexes for commonly queried fields
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_price_history_product_store 
            ON price_history (product_id, store_id, captured_at)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_basket_items_basket 
            ON basket_items (basket_id)
        """))
    
    yield engine
    
    # Properly dispose of the engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Create a test database session."""
    session = Session(test_engine)
    yield session
    session.close()


@pytest.fixture
def store(db_session):
    """Create a test store."""
    store = Store(
        store_id="store123",
        name="Test Store",
        address="123 Test St",
        postal_code="12345",
        latitude=37.7749,
        longitude=-122.4194
    )
    db_session.add(store)
    db_session.commit()
    return store


@pytest.fixture
def category(db_session):
    """Create a test category."""
    category = Category(name="Test Category")
    db_session.add(category)
    db_session.commit()
    return category


@pytest.fixture
def product(db_session, category):
    """Create a test product."""
    product = Product(
        product_id="prod123",
        name="Test Product",
        category_id=category.id
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def basket(db_session, store, test_time):
    """Create a test basket with fixed creation time."""
    basket = Basket(
        name="Test Basket",
        store_id=store.store_id,
        created_at=test_time
    )
    db_session.add(basket)
    db_session.commit()
    return basket


@pytest.fixture
def basket_with_item(db_session, basket, product, test_time):
    """Create a basket with one item and price history."""
    item = BasketItem(
        basket_id=basket.id,
        product_id=product.product_id,
        quantity=1
    )
    db_session.add(item)
    
    # Add base price at basket creation
    base_price = PriceHistory(
        product_id=product.product_id,
        store_id=basket.store_id,
        price=10.0,
        captured_at=test_time
    )
    db_session.add(base_price)
    
    # Add current price (10% increase)
    current_price = PriceHistory(
        product_id=product.product_id,
        store_id=basket.store_id,
        price=11.0,
        captured_at=test_time + timedelta(days=19)
    )
    db_session.add(current_price)
    
    db_session.commit()
    return basket


@pytest.fixture
def mock_kroger_api(monkeypatch):
    """Mock the Kroger API responses."""
    class MockResponse:
        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

        def raise_for_status(self):
            pass

    class MockRequests:
        def __init__(self):
            self.post_data = {
                "access_token": "mock_token",
                "expires_in": 3600
            }
            self.get_data = {
                "data": [{
                    "locationId": "store123",
                    "name": "Test Store",
                    "address": {
                        "addressLine1": "123 Test St",
                        "zipCode": "12345"
                    },
                    "geolocation": {
                        "latitude": 37.7749,
                        "longitude": -122.4194
                    }
                }]
            }

        def post(self, *args, **kwargs):
            return MockResponse(self.post_data)

        def get(self, url, *args, **kwargs):
            if "/products/" in url:
                # Price endpoint
                return MockResponse({
                    "data": [{
                        "productId": "prod123",
                        "items": [{
                            "price": {
                                "regular": 11.00,
                                "promo": None
                            }
                        }]
                    }]
                })
            elif "filter.term" in url:
                # Search endpoint
                return MockResponse({
                    "data": [{
                        "productId": "prod123",
                        "upc": "1234567890",
                        "description": "Test Product",
                        "brand": "Test Brand",
                        "size": "12 oz",
                        "images": [{
                            "url": "http://example.com/image.jpg"
                        }]
                    }]
                })
            return MockResponse(self.get_data)

        def request(self, method, url, *args, **kwargs):
            if method.upper() == "POST":
                return self.post(url, *args, **kwargs)
            return self.get(url, *args, **kwargs)

        def find_stores(self, zip_code: str, limit: int = 5):
            """Mock find_stores method."""
            return self.get_data["data"]

        def search_products(self, term: str, location_id: str, limit: int = 10):
            """Mock search_products method."""
            response = self.get("products?filter.term=" + term).json()
            return response["data"]

        def get_product_prices(self, product_ids: list, store_id: str):
            """Mock get_product_prices method."""
            prices = {}
            for product_id in product_ids:
                response = self.get(f"/products/{product_id}").json()
                if "data" in response and response["data"] and response["data"][0]["items"]:
                    prices[product_id] = float(response["data"][0]["items"][0]["price"]["regular"])
            return prices

    monkeypatch.setattr("basketcase.api.requests", MockRequests())
    return MockRequests()
