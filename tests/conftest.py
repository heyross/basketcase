"""Test fixtures and configuration."""
import os
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Add the parent directory to Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from basketcase.models import Base


@pytest.fixture
def temp_db_path():
    """Create a temporary database file."""
    import tempfile
    import os
    
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
    from sqlalchemy import create_engine
    from basketcase.models import Base
    
    engine = create_engine(f"sqlite:///{temp_db_path}", echo=False)
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Properly dispose of the engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Create a test database session."""
    from sqlalchemy.orm import Session
    
    with Session(test_engine) as session:
        yield session
        # Always rollback at the end of each test
        session.rollback()


@pytest.fixture(autouse=True)
def clean_tables(db_session):
    """Clean all tables before each test."""
    from basketcase.models import Base
    from sqlalchemy import text
    
    # Start with a clean session
    db_session.rollback()
    
    # Drop all tables in reverse order to handle foreign keys
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(text(f"DELETE FROM {table.name}"))
    
    db_session.commit()
    
    yield
    
    # Clean up after test
    db_session.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(text(f"DELETE FROM {table.name}"))
    db_session.commit()


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
                    },
                    "productId": "prod123",
                    "description": "Test Product",
                    "items": [{
                        "price": {
                            "regular": 1.99,
                            "promo": 0.99
                        }
                    }]
                }]
            }

        def post(self, *args, **kwargs):
            return MockResponse(self.post_data)

        def get(self, url, *args, **kwargs):
            if "/products/" in url:
                return MockResponse({
                    "data": [{
                        "productId": "prod123",
                        "items": [{
                            "price": {
                                "regular": 1.99,
                                "promo": 0.99
                            }
                        }]
                    }]
                })
            return MockResponse(self.get_data)

        def request(self, method, url, *args, **kwargs):
            if method == "POST":
                return self.post(url, *args, **kwargs)
            return self.get(url, *args, **kwargs)

    monkeypatch.setattr("basketcase.api.requests", MockRequests())
