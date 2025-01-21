"""Test cases for price update scheduler."""
from datetime import datetime, timezone

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


@pytest.fixture
def test_time():
    """Create a test time."""
    return datetime.now(timezone.utc)


def test_get_active_products(db_session, basket_with_item):
    """Test retrieving active products."""
    scheduler = PriceUpdateScheduler()
    products = scheduler.get_active_products(db_session)
    assert len(products) > 0
    assert isinstance(products[0], tuple)
    assert len(products[0]) == 2
    assert products[0][0] == "prod123"  # product_id
    assert products[0][1] == "store123"  # store_id


def test_update_prices(db_session, store, product, test_time, mocker):
    """Test price update functionality."""
    # Create basket first
    basket = Basket(
        name="Test Basket",
        store_id=store.store_id,
        created_at=test_time
    )
    db_session.add(basket)
    db_session.commit()

    # Now add the basket item
    basket_item = BasketItem(
        basket_id=basket.id,
        product_id=product.product_id,
        quantity=1
    )
    db_session.add(basket_item)
    db_session.commit()

    # Get initial price count
    initial_count = db_session.query(PriceHistory).count()

    # Mock API response with float prices
    mock_api = mocker.Mock()
    mock_api.get_product_prices.return_value = [{
        "productId": "prod123",
        "items": [{
            "price": {
                "regular": 12.99,
                "promo": None
            }
        }]
    }]

    # Create and run scheduler
    scheduler = PriceUpdateScheduler(mock_api)
    scheduler.update_prices(db_session)

    # Verify price was added
    final_count = db_session.query(PriceHistory).count()
    assert final_count == initial_count + 1

    # Verify price details
    latest_price = (
        db_session.query(PriceHistory)
        .filter(
            PriceHistory.product_id == product.product_id,
            PriceHistory.store_id == store.store_id
        )
        .order_by(PriceHistory.captured_at.desc())
        .first()
    )
    assert latest_price is not None
    assert latest_price.price == 12.99
    assert latest_price.promo_price is None
