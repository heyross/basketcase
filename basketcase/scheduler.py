"""Scheduler for periodic price updates."""
import logging
from datetime import datetime, timezone
from typing import List, Optional

import schedule
import time
from sqlalchemy import select
from sqlalchemy.orm import Session

from basketcase.api import KrogerAPI
from basketcase.database import db_session
from basketcase.models import Basket, BasketItem, PriceHistory, Product, Store
from basketcase.services import ErrorService, ProductService


class PriceUpdateScheduler:
    """Scheduler for updating product prices."""

    def __init__(self, api: Optional[KrogerAPI] = None):
        """Initialize the scheduler."""
        self.api = api or KrogerAPI()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_active_products(self, session: Session) -> List[tuple[str, str]]:
        """Get products that need price updates."""
        # Get all unique product-store combinations from baskets
        stmt = (
            select(BasketItem.product_id, Basket.store_id)
            .join(Basket)
            .distinct()
        )
        results = session.execute(stmt).all()
        return [(row[0], row[1]) for row in results]  # Convert Row objects to tuples

    def update_prices(self, session: Optional[Session] = None) -> None:
        """Update prices for all active products."""
        self.logger.info("Starting price update job")
        if session is None:
            with db_session() as session:
                self._update_prices(session)
        else:
            self._update_prices(session)

    def _update_prices(self, session: Session) -> None:
        """Internal method to update prices."""
        try:
            products = self.get_active_products(session)
            updated_count = 0
            
            # Group products by store for batch updates
            store_products = {}
            for product_id, store_id in products:
                if store_id not in store_products:
                    store_products[store_id] = []
                store_products[store_id].append(product_id)
            
            # Update prices for each store's products
            for store_id, product_ids in store_products.items():
                try:
                    prices_data = self.api.get_product_prices(product_ids, store_id)
                    for price_data in prices_data:
                        if not isinstance(price_data, dict) or "items" not in price_data:
                            continue
                            
                        product_id = price_data.get("productId")
                        if not product_id:
                            continue
                            
                        items = price_data.get("items", [])
                        if not items:
                            continue
                            
                        price_info = items[0].get("price", {})
                        regular_price = price_info.get("regular")
                        promo_price = price_info.get("promo")
                        
                        if not regular_price:
                            continue
                            
                        # Create price history entry with UTC timestamp
                        price_history = PriceHistory(
                            product_id=product_id,
                            store_id=store_id,
                            price=float(regular_price),
                            promo_price=float(promo_price) if promo_price else None,
                            captured_at=datetime.now(timezone.utc)
                        )
                        session.add(price_history)
                        updated_count += 1
                        self.logger.info(f"Updated price for product {product_id} at store {store_id}")
                    
                    # Commit after each store's batch
                    session.commit()
                    
                except Exception as e:
                    ErrorService(session).log_error(
                        "ERROR",
                        "SCHEDULER",
                        f"Failed to update prices for store {store_id}",
                        str(e)
                    )
                    self.logger.error(f"Failed to update prices for store {store_id}: {e}")
                    session.rollback()
                    continue

            self.logger.info(f"Updated prices for {updated_count} products")
            
        except Exception as e:
            ErrorService(session).log_error(
                "ERROR",
                "SCHEDULER",
                "Failed to run price update job",
                str(e)
            )
            self.logger.error(f"Price update job failed: {str(e)}")
            session.rollback()

    def run(self) -> None:
        """Run the scheduler."""
        schedule.every().monday.at("00:00").do(self.update_prices)
        
        self.logger.info("Scheduler started")
        while True:
            schedule.run_pending()
            time.sleep(60)
