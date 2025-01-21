"""Business logic services."""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from basketcase.api import KrogerAPI
from basketcase.models import (Basket, BasketItem, Category, ErrorLog,
                             InflationIndex, PriceHistory, Product, Store)

logger = logging.getLogger(__name__)

class StoreService:
    """Service for store-related operations."""

    def __init__(self, db: Session, api: KrogerAPI):
        self.db = db
        self.api = api

    def find_nearby_stores(self, postal_code: str, limit: int = 5) -> List[Store]:
        """Find and save nearby stores."""
        logger.info(f"Finding stores near {postal_code}")
        stores_data = self.api.find_stores(postal_code, limit)
        stores = []

        for store_data in stores_data:
            try:
                logger.debug(f"Processing store data: {store_data}")
                
                # Extract address data safely
                address_data = store_data.get("address", {})
                address_line = address_data.get("addressLine1", "")
                zip_code = address_data.get("zipCode", "")
                
                # Extract geolocation data safely
                geo_data = store_data.get("geolocation", {})
                latitude = geo_data.get("latitude", 0.0)
                longitude = geo_data.get("longitude", 0.0)
                
                store = Store(
                    id=store_data.get("locationId", ""),
                    name=store_data.get("name", ""),
                    address=address_line,
                    postal_code=zip_code,
                    latitude=float(latitude) if latitude else 0.0,
                    longitude=float(longitude) if longitude else 0.0
                )
                logger.debug(f"Created store object: {store}")
                self.db.merge(store)
                stores.append(store)
            except Exception as e:
                logger.error(f"Error processing store data: {e}", exc_info=True)
                continue

        if stores:
            logger.info(f"Found {len(stores)} stores")
            self.db.commit()
        else:
            logger.warning("No stores found")
            
        return stores


class ProductService:
    """Service for product-related operations."""

    def __init__(self, db: Session, api: KrogerAPI):
        self.db = db
        self.api = api

    def search_products(
        self, term: str, store_id: str, limit: int = 10
    ) -> List[Product]:
        """Search for products and save them."""
        products_data = self.api.search_products(term, store_id, limit)
        products = []

        for product_data in products_data:
            try:
                product = Product(
                    product_id=product_data["productId"],
                    upc=product_data.get("upc"),
                    name=product_data["description"],
                    brand=product_data.get("brand"),
                    size=product_data.get("size"),
                    image_url=product_data.get("images", [{}])[0].get("url")
                )
                self.db.merge(product)
                products.append(product)
            except KeyError as e:
                print(f"Warning: Missing required field in product data: {e}")
                print(f"Product data: {product_data}")
                continue

        self.db.commit()
        return products

    def update_prices(
        self, product_ids: List[str], store_id: str
    ) -> None:
        """Update prices for products."""
        prices_data = self.api.get_product_prices(product_ids, store_id)
        now = datetime.now(timezone.utc)
        
        for price_data in prices_data:
            if not price_data.get("items"):
                continue
                
            product_id = price_data["productId"]
            items = price_data["items"]
            if not items:
                continue
                
            price_info = items[0].get("price", {})
            regular_price = price_info.get("regular")
            promo_price = price_info.get("promo")
            
            if not regular_price:
                continue
                
            price_history = PriceHistory(
                product_id=product_id,
                store_id=store_id,
                price=float(regular_price),
                promo_price=float(promo_price) if promo_price else None,
                captured_at=now
            )
            self.db.add(price_history)
            
        self.db.commit()

    def get_product_prices(
        self, product_ids: List[str], store_id: str
    ) -> List[PriceHistory]:
        """Get prices for products."""
        stmt = (
            select(PriceHistory)
            .filter(
                PriceHistory.product_id.in_(product_ids),
                PriceHistory.store_id == store_id
            )
            .order_by(PriceHistory.captured_at.desc())
        )
        return self.db.execute(stmt).scalars().all()


class BasketService:
    """Service for basket-related operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_basket(
        self, name: str, store_id: str, is_template: bool = False
    ) -> Basket:
        """Create a new basket."""
        basket = Basket(
            name=name,
            store_id=store_id,
            is_template=is_template,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(basket)
        self.db.commit()
        return basket

    def add_to_basket(
        self, basket_id: int, product_id: str, quantity: int = 1
    ) -> BasketItem:
        """Add a product to a basket."""
        basket = self.db.query(Basket).get(basket_id)
        if not basket:
            raise ValueError("Basket not found")

        if len(basket.items) >= 50:
            raise ValueError("Basket is full (max 50 items)")

        # Check if item already exists
        existing = self.db.scalar(
            select(BasketItem).where(
                BasketItem.basket_id == basket_id,
                BasketItem.product_id == product_id
            )
        )
        if existing:
            existing.quantity = quantity
            self.db.commit()
            return existing

        item = BasketItem(
            basket_id=basket_id,
            product_id=product_id,
            quantity=quantity,
            added_at=datetime.now(timezone.utc)
        )
        self.db.add(item)
        self.db.commit()
        return item

    def clone_basket(self, basket_id: int, new_name: str) -> Basket:
        """Clone an existing basket."""
        original = self.db.query(Basket).get(basket_id)
        if not original:
            raise ValueError(f"Basket {basket_id} not found")

        clone = Basket(
            name=new_name,
            store_id=original.store_id,
            is_template=False,
            parent_basket_id=original.id,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(clone)
        self.db.flush()  # Get clone.id

        for item in original.items:
            clone_item = BasketItem(
                basket_id=clone.id,
                product_id=item.product_id,
                quantity=item.quantity,
                added_at=datetime.now(timezone.utc)
            )
            self.db.add(clone_item)

        self.db.commit()
        return clone


class InflationService:
    """Service for inflation calculations."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_basket_inflation(
        self, basket_id: int
    ) -> Tuple[float, datetime]:
        """Calculate inflation for a basket.
        
        Args:
            basket_id: ID of the basket to calculate inflation for
            
        Returns:
            Tuple[float, datetime]: (inflation percentage, calculation timestamp)
            
        Raises:
            ValueError: If basket not found or has no items
        """
        print(f"\n=== Starting Inflation Calculation for Basket {basket_id} ===")
        now = datetime.now(timezone.utc)
        
        # Get basket and items
        basket = self.db.query(Basket).get(basket_id)
        if not basket:
            raise ValueError(f"Basket {basket_id} not found")
            
        print(f"Found basket: {basket.name} created at {basket.created_at}")
        
        if not basket.items:
            raise ValueError(f"Basket {basket_id} has no items")
            
        print(f"Found {len(basket.items)} items in basket")
        print(f"Current time: {now}")
        
        # Get all product IDs
        product_ids = [item.product_id for item in basket.items]
        print(f"\nFetching prices for products: {product_ids}")
        
        # Get all prices for these products
        stmt = (
            select(PriceHistory)
            .filter(
                PriceHistory.product_id.in_(product_ids),
                PriceHistory.store_id == basket.store_id
            )
            .order_by(PriceHistory.captured_at)
        )
        all_prices = self.db.execute(stmt).scalars().all()
        
        for price in all_prices:
            print(f"Price {price.price} for product {price.product_id} at {price.captured_at}")
        
        # Calculate total values
        total_base_value = 0.0
        total_current_value = 0.0
        base_date = None
        
        print("\n=== Processing Each Item ===")
        for item in basket.items:
            print(f"\nItem: product={item.product_id}, quantity={item.quantity}")
            
            # Get all prices for this product
            product_prices = [p for p in all_prices if p.product_id == item.product_id]
            if not product_prices:
                print("WARNING: No prices found for product, skipping")
                continue
                
            # Get base price (closest before basket creation)
            earliest_prices = sorted(
                [p for p in product_prices if p.captured_at <= basket.created_at],
                key=lambda p: p.captured_at
            )
            print(f"Found {len(earliest_prices)} prices before basket creation:")
            for p in earliest_prices:
                print(f"  Price: {p.price} at {p.captured_at}")
                
            base_price = earliest_prices[0] if earliest_prices else None
            
            # Get current price (most recent)
            current_prices = sorted(product_prices, key=lambda p: p.captured_at, reverse=True)
            print(f"Found {len(current_prices)} prices for current value:")
            for p in current_prices:
                print(f"  Price: {p.price} at {p.captured_at}")
            
            current_price = current_prices[0] if current_prices else None
            
            if not base_price or not current_price:
                print("WARNING: Missing base or current price, skipping item")
                continue
                
            # Update base date to earliest price date found
            if base_date is None or base_price.captured_at < base_date:
                base_date = base_price.captured_at
                print(f"Updated base date to {base_date}")
                
            # Calculate weighted values
            item_base_value = base_price.price * item.quantity
            item_current_value = current_price.price * item.quantity
            print(f"Base value: {item_base_value} (price={base_price.price} * quantity={item.quantity})")
            print(f"Current value: {item_current_value} (price={current_price.price} * quantity={item.quantity})")
            
            total_base_value += item_base_value
            total_current_value += item_current_value
        
        print(f"\n=== Final Calculations ===")
        print(f"Total base value: {total_base_value}")
        print(f"Total current value: {total_current_value}")
        
        if total_base_value == 0:
            print("WARNING: No valid prices found, returning 0% inflation")
            self._update_inflation_index(basket_id, 0.0, basket.created_at, now)
            return 0.0, now
            
        # Calculate percentage change
        inflation = ((total_current_value / total_base_value) - 1.0) * 100.0
        print(f"Calculated inflation: {inflation}%")
        
        # Use the earliest price date as base date, fallback to basket creation
        base_date = base_date or basket.created_at
        print(f"Final base date: {base_date}")
        
        # Update index and return
        print("\n=== Updating Index ===")
        self._update_inflation_index(basket_id, inflation, base_date, now)
        print("Index updated successfully")
        
        return inflation, now

    def _update_inflation_index(
        self,
        basket_id: int,
        inflation: float,
        base_date: datetime,
        calculation_time: datetime
    ) -> None:
        """Update or create inflation index."""
        print(f"Updating index for basket {basket_id}")
        print(f"Inflation: {inflation}%")
        print(f"Base date: {base_date}")
        print(f"Calculation time: {calculation_time}")
        
        try:
            index = (
                self.db.query(InflationIndex)
                .filter(InflationIndex.basket_id == basket_id)
                .first()
            )
            
            if index:
                print("Updating existing index")
                index.base_index = 100.0
                index.current_index = 100.0 + inflation
                index.base_date = base_date
                index.calculation_time = calculation_time
            else:
                print("Creating new index")
                index = InflationIndex(
                    basket_id=basket_id,
                    base_index=100.0,
                    current_index=100.0 + inflation,
                    base_date=base_date,
                    calculation_time=calculation_time
                )
                self.db.add(index)
                
            self.db.commit()
            print("Index saved successfully")
            
        except Exception as e:
            self.db.rollback()
            print(f"ERROR: Failed to update index: {e}")
            raise


class ErrorService:
    """Service for error logging."""

    def __init__(self, db: Session):
        self.db = db

    def log_error(
        self, level: str, component: str, message: str, details: str = None
    ) -> ErrorLog:
        """Log an error to the database."""
        error = ErrorLog(
            level=level,
            component=component,
            message=message,
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(error)
        self.db.commit()
        return error
