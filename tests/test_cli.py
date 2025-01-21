"""Test cases for command-line interface."""
from click.testing import CliRunner

import pytest

from basketcase.cli import cli
from basketcase.models import Basket, Product, Store, PriceHistory, BasketItem, Category


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


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


def test_find_stores(runner, mock_kroger_api):
    """Test find_stores command."""
    result = runner.invoke(cli, ["find-stores", "12345"])
    assert result.exit_code == 0


def test_search_products(runner, mock_kroger_api):
    """Test search_products command."""
    result = runner.invoke(cli, ["search-products", "milk", "store123"])
    assert result.exit_code == 0


def test_create_basket(runner, store):
    """Test create_basket command."""
    result = runner.invoke(cli, ["create-basket", "Test Basket", store.store_id])
    assert result.exit_code == 0
    assert "Created basket" in result.output


def test_add_to_basket(runner, basket, product):
    """Test add_to_basket command."""
    result = runner.invoke(
        cli, ["add-to-basket", str(basket.id), product.product_id, "2"]
    )
    assert result.exit_code == 0
    assert "Added to basket" in result.output


def test_clone_basket(runner, basket):
    """Test clone_basket command."""
    result = runner.invoke(
        cli, ["clone-basket", str(basket.id), "Cloned Basket"]
    )
    assert result.exit_code == 0
    assert "Cloned basket" in result.output


def test_calculate_inflation(runner, db_session):
    """Test calculate_inflation command."""
    from datetime import datetime, timedelta
    from basketcase.models import (
        PriceHistory, BasketItem, Basket, Product, Store, Category
    )
    
    # Create test data with specific timestamps
    base_time = datetime(2025, 1, 1, 0, 0, 0)  # Fixed base time
    current_time = base_time + timedelta(days=30)  # 30 days later
    
    # Create category
    category = Category(name="Test Category")
    db_session.add(category)
    db_session.flush()
    
    # Create store
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
    
    # Create product with category
    product = Product(
        product_id="prod123",
        name="Test Product",
        category_id=category.id
    )
    db_session.add(product)
    db_session.flush()
    
    # Create basket with creation time
    basket = Basket(
        name="Test Basket",
        store_id=store.store_id,
        created_at=base_time
    )
    db_session.add(basket)
    db_session.flush()
    
    # Add item to basket with quantity 1
    basket_item = BasketItem(
        basket_id=basket.id,
        product_id=product.product_id,
        quantity=1
    )
    db_session.add(basket_item)
    db_session.flush()
    
    # Add price history with exact timestamps
    base_price = PriceHistory(
        product_id=product.product_id,
        store_id=store.store_id,
        price=1.00,  # Base price $1.00
        captured_at=base_time
    )
    db_session.add(base_price)
    
    current_price = PriceHistory(
        product_id=product.product_id,
        store_id=store.store_id,
        price=1.10,  # Current price $1.10 (10% increase)
        captured_at=current_time
    )
    db_session.add(current_price)
    db_session.commit()
    
    # Run the inflation calculation
    result = runner.invoke(cli, ["calculate-inflation", str(basket.id)])
    assert result.exit_code == 0
    
    # Verify the output contains both overall and category inflation
    assert "Base Index: 100.0" in result.output
    assert "Current Index: 110.0" in result.output
    assert "Change: +10.0%" in result.output
    assert "Test Category: +10.0%" in result.output


def test_init_command(runner):
    """Test database initialization command."""
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    assert "Database initialized successfully" in result.output
