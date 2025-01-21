"""Test cases for database models."""
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from basketcase.models import (Basket, BasketItem, Category, ErrorLog,
                             InflationIndex, PriceHistory, Product, Store)


def test_store_creation(db_session):
    """Test creating a store."""
    store = Store(
        store_id="test123",
        name="Test Store",
        address="123 Test St",
        postal_code="12345",
        latitude=37.7749,
        longitude=-122.4194
    )
    db_session.add(store)
    db_session.commit()

    assert store.store_id == "test123"
    assert store.name == "Test Store"
    assert store.created_at is not None
    assert store.last_updated is not None


def test_category_creation(db_session):
    """Test creating categories with parent-child relationship."""
    parent = Category(name="Produce")
    child = Category(name="Fruits")
    
    db_session.add(parent)
    db_session.flush()
    
    child.parent_id = parent.id
    db_session.add(child)
    db_session.commit()

    assert child.parent_id == parent.id
    assert child in parent.children


def test_product_creation(db_session):
    """Test creating a product."""
    category = Category(name="Test Category")
    db_session.add(category)
    db_session.flush()

    product = Product(
        product_id="prod123",
        name="Test Product",
        category_id=category.id
    )
    db_session.add(product)
    db_session.commit()

    assert product.product_id == "prod123"
    assert product.category_id == category.id


def test_basket_creation(db_session):
    """Test creating a basket with items."""
    store = Store(
        store_id="store123",
        name="Test Store",
        address="123 Test St",
        postal_code="12345",
        latitude=37.7749,
        longitude=-122.4194
    )
    db_session.add(store)
    db_session.flush()

    basket = Basket(
        name="Test Basket",
        store_id=store.store_id
    )
    db_session.add(basket)
    db_session.commit()

    assert basket.name == "Test Basket"
    assert basket.store_id == store.store_id
    assert not basket.is_template


def test_basket_item_creation(db_session):
    """Test adding items to a basket."""
    store = Store(
        store_id="store123",
        name="Test Store",
        address="123 Test St",
        postal_code="12345",
        latitude=37.7749,
        longitude=-122.4194
    )
    db_session.add(store)
    
    product = Product(
        product_id="prod123",
        name="Test Product"
    )
    db_session.add(product)
    
    basket = Basket(
        name="Test Basket",
        store_id=store.store_id
    )
    db_session.add(basket)
    db_session.flush()

    basket_item = BasketItem(
        basket_id=basket.id,
        product_id=product.product_id,
        quantity=2
    )
    db_session.add(basket_item)
    db_session.commit()

    assert basket_item.quantity == 2
    assert basket_item in basket.items


def test_price_history_creation(db_session):
    """Test recording price history."""
    store = Store(
        store_id="store123",
        name="Test Store",
        address="123 Test St",
        postal_code="12345",
        latitude=37.7749,
        longitude=-122.4194
    )
    db_session.add(store)
    
    product = Product(
        product_id="prod123",
        name="Test Product"
    )
    db_session.add(product)
    db_session.flush()

    price = PriceHistory(
        product_id=product.product_id,
        store_id=store.store_id,
        price=9.99,
        promo_price=7.99
    )
    db_session.add(price)
    db_session.commit()

    assert price.price == 9.99
    assert price.promo_price == 7.99


def test_inflation_index_creation(db_session):
    """Test creating inflation indices."""
    store = Store(
        store_id="store123",
        name="Test Store",
        address="123 Test St",
        postal_code="12345",
        latitude=37.7749,
        longitude=-122.4194
    )
    db_session.add(store)
    
    basket = Basket(
        name="Test Basket",
        store_id=store.store_id
    )
    db_session.add(basket)
    db_session.flush()

    index = InflationIndex(
        basket_id=basket.id,
        base_date=datetime.utcnow(),
        current_index=100.0
    )
    db_session.add(index)
    db_session.commit()

    assert index.current_index == 100.0
    assert index.basket_id == basket.id


def test_error_log_creation(db_session):
    """Test creating error logs."""
    error = ErrorLog(
        level="ERROR",
        component="API",
        message="Test error message",
        details="Error details"
    )
    db_session.add(error)
    db_session.commit()

    assert error.level == "ERROR"
    assert error.component == "API"
    assert not error.resolved


def test_store_unique_constraint(db_session):
    """Test that store IDs must be unique."""
    store1 = Store(
        store_id="store123",
        name="Test Store 1",
        address="123 Test St",
        postal_code="12345",
        latitude=37.7749,
        longitude=-122.4194
    )
    store2 = Store(
        store_id="store123",  # Same ID
        name="Test Store 2",
        address="456 Test Ave",
        postal_code="12345",
        latitude=37.7749,
        longitude=-122.4194
    )
    
    db_session.add(store1)
    db_session.commit()
    
    with pytest.raises(IntegrityError):
        db_session.add(store2)
        db_session.commit()
