"""Test cases for price update scheduler."""
from datetime import datetime

import pytest
from sqlalchemy import select

from basketcase.models import Basket, BasketItem, PriceHistory, Product, Store
from basketcase.scheduler import PriceUpdateScheduler


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
def product(db_session):
    """Create a test product."""
    product = Product(
        product_id="prod123",
        name="Test Product"
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def basket_with_item(db_session, store, product):
    """Create a test basket with an item."""
    basket = Basket(
        name="Test Basket",
        store_id=store.store_id
    )
    db_session.add(basket)
    db_session.flush()

    item = BasketItem(
        basket_id=basket.id,
        product_id=product.product_id,
        quantity=1
    )
    db_session.add(item)
    db_session.commit()
    return basket


def test_get_active_products(db_session, basket_with_item):
    """Test retrieving active products."""
    scheduler = PriceUpdateScheduler()
    products = scheduler.get_active_products(db_session)
    assert len(products) > 0
    assert isinstance(products[0], tuple)
    assert len(products[0]) == 2
    assert products[0][0] == "prod123"  # product_id
    assert products[0][1] == "store123"  # store_id


def test_update_prices(db_session, mock_kroger_api, basket_with_item):
    """Test price update job."""
    scheduler = PriceUpdateScheduler()
    
    # Get initial price history count
    initial_count = db_session.query(PriceHistory).count()
    
    # Run price update
    scheduler.update_prices()
    
    # Verify new price history entries were created
    final_count = db_session.query(PriceHistory).count()
    assert final_count > initial_count
