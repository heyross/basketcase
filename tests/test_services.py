"""Test cases for business logic services."""
from datetime import datetime, timedelta
from dateutil import tz

import pytest

from basketcase.api import KrogerAPI
from basketcase.models import (Basket, BasketItem, InflationIndex, PriceHistory,
                             Product, Store)
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
    service = StoreService(db_session, mock_kroger_api)
    stores = service.find_nearby_stores("12345")
    assert isinstance(stores, list)


def test_product_service(db_session, mock_kroger_api):
    """Test product service operations."""
    service = ProductService(db_session, mock_kroger_api)
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
    """Test inflation calculations with detailed debugging."""
    service = InflationService(db_session)
    
    print("\n=== Database State Before Test ===")
    # Check existing records
    existing_baskets = db_session.query(Basket).all()
    print(f"Existing baskets: {len(existing_baskets)}")
    for b in existing_baskets:
        print(f"  Basket {b.id}: {b.name} created at {b.created_at}")
    
    existing_prices = db_session.query(PriceHistory).all()
    print(f"Existing prices: {len(existing_prices)}")
    for p in existing_prices:
        print(f"  Price {p.price} for product {p.product_id} at {p.captured_at}")
    
    # Set fixed times for test (in UTC)
    base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=tz.tzutc())
    current_time = datetime(2025, 1, 20, 12, 0, 0, tzinfo=tz.tzutc())
    
    # Update basket creation time
    basket.created_at = base_time
    db_session.commit()
    print(f"\nSet basket creation time to {base_time}")
    
    # Add item to basket
    item = BasketItem(
        basket_id=basket.id,
        product_id=product.product_id,
        quantity=2  # Use quantity > 1 to test weighted calculations
    )
    db_session.add(item)
    db_session.commit()
    print(f"\nAdded basket item: quantity={item.quantity}")
    
    # Clear any existing prices
    db_session.query(PriceHistory).delete()
    db_session.commit()
    print("\nCleared existing prices")
    
    # Add base price just before basket creation
    base_price = PriceHistory(
        product_id=product.product_id,
        store_id=basket.store_id,
        price=10.0,
        captured_at=base_time - timedelta(minutes=5)
    )
    db_session.add(base_price)
    db_session.commit()
    print(f"Added base price: {base_price.price} at {base_price.captured_at}")
    
    # Add some intermediate prices to test correct base/current selection
    mid_price = PriceHistory(
        product_id=product.product_id,
        store_id=basket.store_id,
        price=10.5,
        captured_at=base_time + timedelta(days=5)
    )
    db_session.add(mid_price)
    db_session.commit()
    print(f"Added mid price: {mid_price.price} at {mid_price.captured_at}")
    
    # Add current price (10% increase from base)
    current_price = PriceHistory(
        product_id=product.product_id,
        store_id=basket.store_id,
        price=11.0,
        captured_at=current_time
    )
    db_session.add(current_price)
    db_session.commit()
    print(f"Added current price: {current_price.price} at {current_price.captured_at}")
    
    print("\n=== Verifying Test Setup ===")
    # Verify all records were properly saved
    prices = (
        db_session.query(PriceHistory)
        .filter(
            PriceHistory.product_id == product.product_id,
            PriceHistory.store_id == basket.store_id
        )
        .order_by(PriceHistory.captured_at)
        .all()
    )
    assert len(prices) == 3, f"Expected 3 prices, found {len(prices)}"
    for p in prices:
        print(f"Price: {p.price} at {p.captured_at}")
    
    items = (
        db_session.query(BasketItem)
        .filter(BasketItem.basket_id == basket.id)
        .all()
    )
    assert len(items) == 1, f"Expected 1 basket item, found {len(items)}"
    print(f"Basket item: product={items[0].product_id}, quantity={items[0].quantity}")
    
    # Calculate inflation
    print("\n=== Calculating Inflation ===")
    inflation, calc_time = service.calculate_basket_inflation(basket.id)
    print(f"Calculated inflation: {inflation}% at {calc_time}")
    
    # Verify calculations
    expected_base_value = base_price.price * item.quantity
    expected_current_value = current_price.price * item.quantity
    expected_inflation = ((expected_current_value / expected_base_value) - 1.0) * 100.0
    
    print("\n=== Verifying Calculations ===")
    print(f"Base value: {expected_base_value} (price={base_price.price} * quantity={item.quantity})")
    print(f"Current value: {expected_current_value} (price={current_price.price} * quantity={item.quantity})")
    print(f"Expected inflation: {expected_inflation}%")
    print(f"Actual inflation: {inflation}%")
    
    assert abs(inflation - expected_inflation) < 0.01, \
        f"Inflation calculation error: expected {expected_inflation}%, got {inflation}%"
    
    # Verify the index
    print("\n=== Verifying Index ===")
    index = (
        db_session.query(InflationIndex)
        .filter(InflationIndex.basket_id == basket.id)
        .first()
    )
    assert index is not None, "No inflation index was created"
    print(f"Index found: base={index.base_index}, current={index.current_index}")
    print(f"Base date: {index.base_date}")
    print(f"Calc time: {index.calculation_time}")
    
    assert index.base_index == 100.0, \
        f"Expected base index 100.0, got {index.base_index}"
    assert abs(index.current_index - 110.0) < 0.01, \
        f"Expected current index 110.0, got {index.current_index}"
    assert index.base_date == base_price.captured_at, \
        f"Expected base date {base_price.captured_at}, got {index.base_date}"
    
    print("\n=== Test Complete ===")


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
    assert error.message == "Test error message"
    assert error.details == "Error details"
