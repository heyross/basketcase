"""Scheduler for periodic price updates."""
import logging
from datetime import datetime
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

    def __init__(self):
        """Initialize the scheduler."""
        self.api = KrogerAPI()
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

    def update_prices(self) -> None:
        """Update prices for all active products."""
        self.logger.info("Starting price update job")
        with db_session() as session:
            try:
                products = self.get_active_products(session)
                updated_count = 0
                for product_id, store_id in products:
                    try:
                        prices = self.api.get_product_prices([product_id], store_id)
                        if product_id in prices:
                            price = PriceHistory(
                                product_id=product_id,
                                store_id=store_id,
                                price=prices[product_id],
                                captured_at=datetime.now()
                            )
                            session.add(price)
                            session.commit()
                            updated_count += 1
                            self.logger.info(f"Updated price for product {product_id} at store {store_id}")
                    except Exception as e:
                        ErrorService(session).log_error(
                            "ERROR",
                            "SCHEDULER",
                            f"Failed to update price for product {product_id}",
                            str(e)
                        )
                        self.logger.error(f"Failed to update price for product {product_id}: {e}")
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

    def run(self) -> None:
        """Run the scheduler."""
        schedule.every().monday.at("00:00").do(self.update_prices)
        
        self.logger.info("Scheduler started")
        while True:
            schedule.run_pending()
            time.sleep(60)
