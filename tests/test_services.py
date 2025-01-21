"""Test cases for business logic services."""
from datetime import datetime, timedelta

import pytest

from basketcase.api import KrogerAPI
from basketcase.models import Basket, BasketItem, PriceHistory, Product, Store
from basketcase.services import (BasketService, ErrorService, InflationService,
                               ProductService, StoreService)


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
def basket(db_session, store):
    """Create a test basket."""
    basket = Basket(
        name="Test Basket",
        store_id=store.store_id
    )
    db_session.add(basket)
    db_session.commit()
    return basket


def test_store_service(db_session, mock_kroger_api):
    """Test store service operations."""
    service = StoreService(db_session, KrogerAPI())
    stores = service.find_nearby_stores("12345")
    assert isinstance(stores, list)


def test_product_service(db_session, mock_kroger_api):
    """Test product service operations."""
    service = ProductService(db_session, KrogerAPI())
    products = service.search_products("milk", "store123")
    assert isinstance(products, list)


def test_basket_service_create(db_session, store):
    """Test basket creation."""
    service = BasketService(db_session)
    basket = service.create_basket("Test Basket", store.store_id)
    assert basket.name == "Test Basket"
    assert basket.store_id == store.store_id


def test_basket_service_add_item(db_session, basket, product):
    """Test adding items to basket."""
    service = BasketService(db_session)
    item = service.add_to_basket(basket.id, product.product_id, 2)
    assert item.quantity == 2
    assert item.basket_id == basket.id


def test_basket_service_clone(db_session, basket, product):
    """Test basket cloning."""
    # Add item to original basket
    service = BasketService(db_session)
    service.add_to_basket(basket.id, product.product_id, 2)
    
    # Clone basket
    clone = service.clone_basket(basket.id, "Cloned Basket")
    assert clone.name == "Cloned Basket"
    assert clone.parent_basket_id == basket.id
    assert len(clone.items) == len(basket.items)


def test_basket_item_limit(db_session, basket):
    """Test basket item limit."""
    service = BasketService(db_session)
    
    # Create 50 different products and add them to the basket
    for i in range(50):
        product = Product(
            product_id=f"prod{i}",
            name=f"Product {i}"
        )
        db_session.add(product)
    db_session.commit()

    # Add 50 items (should succeed)
    for i in range(50):
        service.add_to_basket(basket.id, f"prod{i}")

    # Try to add 51st item (should fail)
    product = Product(
        product_id="prod51",
        name="Product 51"
    )
    db_session.add(product)
    db_session.commit()

    with pytest.raises(ValueError, match="Basket is full"):
        service.add_to_basket(basket.id, "prod51")


def test_inflation_service(db_session, basket, product):
    """Test inflation calculations."""
    service = InflationService(db_session)
    
    # Add item to basket
    basket_item = BasketItem(
        basket_id=basket.id,
        product_id=product.product_id,
        quantity=1
    )
    db_session.add(basket_item)

    # Add historical price
    base_price = PriceHistory(
        product_id=product.product_id,
        store_id=basket.store_id,
        price=10.0,
        captured_at=basket.created_at
    )
    db_session.add(base_price)

    # Add current price (10% increase)
    current_price = PriceHistory(
        product_id=product.product_id,
        store_id=basket.store_id,
        price=11.0,
        captured_at=datetime.utcnow()
    )
    db_session.add(current_price)
    db_session.commit()

    # Calculate inflation
    index, _ = service.calculate_basket_inflation(basket.id)
    assert index == 10.0  # 10% increase from base price


def test_error_service(db_session):
    """Test error logging."""
    service = ErrorService(db_session)
    error = service.log_error(
        "ERROR",
        "TEST",
        "Test error message",
        "Error details"
    )
    assert error.level == "ERROR"
    assert error.component == "TEST"
    assert not error.resolved
