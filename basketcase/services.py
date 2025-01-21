"""Business logic services."""
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from basketcase.api import KrogerAPI
from basketcase.models import (Basket, BasketItem, Category, ErrorLog,
                             InflationIndex, PriceHistory, Product, Store)


class StoreService:
    """Service for store-related operations."""

    def __init__(self, db: Session, api: KrogerAPI):
        self.db = db
        self.api = api

    def find_nearby_stores(self, postal_code: str, limit: int = 5) -> List[Store]:
        """Find and save nearby stores."""
        stores_data = self.api.find_stores(postal_code, limit)
        stores = []

        for store_data in stores_data:
            store = Store(
                store_id=store_data["locationId"],
                name=store_data["name"],
                address=store_data["address"]["addressLine1"],
                postal_code=store_data["address"]["zipCode"],
                latitude=store_data["geolocation"]["latitude"],
                longitude=store_data["geolocation"]["longitude"],
                hours=store_data.get("hours", {}).get("operating", "")
            )
            self.db.merge(store)
            stores.append(store)

        self.db.commit()
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

        self.db.commit()
        return products

    def update_prices(
        self, product_ids: List[str], store_id: str
    ) -> None:
        """Update prices for products."""
        prices = self.api.get_product_prices(product_ids, store_id)
        now = datetime.now()
        
        for product_id, price in prices.items():
            history = PriceHistory(
                product_id=product_id,
                store_id=store_id,
                price=price,
                captured_at=now
            )
            self.db.add(history)
        
        self.db.commit()

    def get_product_prices(
        self, product_ids: List[str], store_id: str
    ) -> List[PriceHistory]:
        """Get prices for products."""
        prices_data = self.api.get_product_prices(product_ids, store_id)
        price_history = []

        for price_data in prices_data:
            price = PriceHistory(
                product_id=price_data["productId"],
                store_id=store_id,
                price=float(price_data["items"][0]["price"]["regular"]),
                promo_price=float(price_data["items"][0]["price"].get("promo", 0))
                if "promo" in price_data["items"][0]["price"]
                else None,
                captured_at=datetime.now()
            )
            self.db.add(price)
            price_history.append(price)

        self.db.commit()
        return price_history


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
            is_template=is_template
        )
        self.db.add(basket)
        self.db.commit()
        return basket

    def add_to_basket(
        self, basket_id: int, product_id: str, quantity: int = 1
    ) -> BasketItem:
        """Add a product to a basket."""
        basket = self.db.get(Basket, basket_id)
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
            quantity=quantity
        )
        self.db.add(item)
        self.db.commit()
        return item

    def clone_basket(self, basket_id: int, new_name: str) -> Basket:
        """Clone an existing basket."""
        original = self.db.get(Basket, basket_id)
        if not original:
            raise ValueError("Original basket not found")

        clone = Basket(
            name=new_name,
            store_id=original.store_id,
            parent_basket_id=original.id
        )
        self.db.add(clone)
        self.db.flush()

        for item in original.items:
            clone_item = BasketItem(
                basket_id=clone.id,
                product_id=item.product_id,
                quantity=item.quantity
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
        """Calculate inflation for a basket."""
        # Get basket and items
        stmt = (
            select(Basket)
            .options(joinedload(Basket.items))
            .where(Basket.id == basket_id)
        )
        basket = self.db.scalar(stmt)
        if not basket:
            raise ValueError(f"Basket {basket_id} not found")

        total_old = 0.0
        total_new = 0.0
        now = datetime.now()

        # Get price history for basket items
        for item in basket.items:
            # Get oldest and newest prices for this item
            prices = (
                self.db.query(PriceHistory)
                .filter(
                    PriceHistory.product_id == item.product_id,
                    PriceHistory.store_id == basket.store_id
                )
                .order_by(PriceHistory.captured_at)
                .all()
            )
            
            if not prices:
                continue

            # Calculate weighted prices (price * quantity)
            oldest_price = prices[0].price
            newest_price = prices[-1].price
            total_old += oldest_price * item.quantity
            total_new += newest_price * item.quantity

        if total_old == 0:
            return 0.0, now

        # Calculate percentage change
        inflation = ((total_new - total_old) / total_old) * 100.0
        return inflation, now


class ErrorService:
    """Service for error logging."""

    def __init__(self, db: Session):
        self.db = db

    def log_error(
        self, level: str, component: str, message: str, details: Optional[str] = None
    ) -> ErrorLog:
        """Log an error."""
        error = ErrorLog(
            level=level,
            component=component,
            message=message,
            details=details,
            logged_at=datetime.now()
        )
        self.db.add(error)
        self.db.commit()
        return error
