"""Test cases for command-line interface."""
from click.testing import CliRunner
from datetime import datetime

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
    """Test inflation calculation command."""
    # Create test data
    store = Store(
        store_id="store123",
        name="Test Store",
        address="123 Test St",
        postal_code="12345",
        latitude=0.0,
        longitude=0.0
    )
    db_session.add(store)

    product = Product(
        product_id="prod123",
        name="Test Product",
        brand="Test Brand"
    )
    db_session.add(product)

    basket = Basket(
        name="Test Basket",
        store_id=store.store_id
    )
    db_session.add(basket)
    db_session.flush()  # Get basket ID

    basket_item = BasketItem(
        basket_id=basket.id,
        product_id=product.product_id,
        quantity=1
    )
    db_session.add(basket_item)

    # Add base price
    base_price = PriceHistory(
        product_id=product.product_id,
        store_id=store.store_id,
        price=10.0,
        captured_at=basket.created_at
    )
    db_session.add(base_price)

    # Add current price (10% increase)
    current_price = PriceHistory(
        product_id=product.product_id,
        store_id=store.store_id,
        price=11.0,
        captured_at=datetime.utcnow()
    )
    db_session.add(current_price)
    db_session.commit()

    # Run command
    result = runner.invoke(cli, ["calculate-inflation", str(basket.id)])
    assert result.exit_code == 0
    assert "Current Index: 110.0" in result.output
    assert "Change: +10.0%" in result.output


def test_init_command(runner):
    """Test database initialization command."""
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    assert "Database initialized successfully" in result.output
