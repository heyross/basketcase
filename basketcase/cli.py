"""Command-line interface for the application."""
import click
import logging
import sys
from sqlalchemy.orm import Session

from basketcase.api import KrogerAPI
from basketcase.database import db_session, init_db
from basketcase.models import Basket, Category, InflationIndex
from basketcase.services import (BasketService, ErrorService, InflationService,
                               ProductService, StoreService)
from basketcase.config import LOG_LEVEL

# Set up logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('basketcase.log')
    ]
)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Basketcase - Track grocery prices and calculate inflation."""
    pass


@cli.command()
@click.argument("postal_code")
def find_stores(postal_code: str):
    """Find nearby Kroger stores."""
    with db_session() as db:
        try:
            logger.info(f"Finding stores near {postal_code}")
            api = KrogerAPI()
            logger.info("Initializing API client...")
            logger.debug(f"Base URL: {api.base_url}")
            service = StoreService(db, api)
            logger.info("Finding stores...")
            stores = service.find_nearby_stores(postal_code)
            
            if not stores:
                logger.warning("No stores found")
                click.echo("No stores found in your area.")
                return
                
            click.echo("\nNearby Stores:")
            for store in stores:
                click.echo(
                    f"\nStore ID: {store.id}"
                    f"\nName: {store.name}"
                    f"\nAddress: {store.address}"
                    f"\nPostal Code: {store.postal_code}"
                )
        except Exception as e:
            logger.error(f"Error finding stores: {str(e)}", exc_info=True)
            ErrorService(db).log_error("ERROR", "CLI", str(e))
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
@click.argument("term")
@click.argument("store_id")
def search_products(term: str, store_id: str):
    """Search for products at a store."""
    with db_session() as db:
        try:
            logger.info(f"Searching for '{term}' at store {store_id}")
            api = KrogerAPI()
            service = ProductService(db, api)
            products = service.search_products(term, store_id)
            
            if not products:
                logger.warning("No products found")
                click.echo("No products found matching your search.")
                return
                
            click.echo("\nProducts Found:")
            for product in products:
                click.echo(
                    f"\nProduct ID: {product.id}"
                    f"\nName: {product.name}"
                    f"\nBrand: {product.brand}"
                    f"\nPrice: ${product.price:.2f}"
                )
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}", exc_info=True)
            ErrorService(db).log_error("ERROR", "CLI", str(e))
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
@click.argument("name")
@click.argument("store_id")
def create_basket(name: str, store_id: str):
    """Create a new basket."""
    with db_session() as db:
        try:
            logger.info(f"Creating basket: {name} at store {store_id}")
            service = BasketService(db)
            basket = service.create_basket(name, store_id)
            click.echo(f"\nCreated basket: {basket.name} (ID: {basket.id})")
        except Exception as e:
            logger.error(f"Error creating basket: {str(e)}", exc_info=True)
            ErrorService(db).log_error("ERROR", "CLI", str(e))
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
@click.argument("basket_id", type=int)
@click.argument("product_id")
@click.argument("quantity", type=int, default=1)
def add_to_basket(basket_id: int, product_id: str, quantity: int):
    """Add a product to a basket."""
    with db_session() as db:
        try:
            logger.info(f"Adding product {product_id} to basket {basket_id} with quantity {quantity}")
            service = BasketService(db)
            item = service.add_to_basket(basket_id, product_id, quantity)
            click.echo(
                f"\nAdded to basket:"
                f"\nProduct ID: {item.product_id}"
                f"\nQuantity: {item.quantity}"
            )
        except Exception as e:
            logger.error(f"Error adding to basket: {str(e)}", exc_info=True)
            ErrorService(db).log_error("ERROR", "CLI", str(e))
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
@click.argument("basket_id", type=int)
@click.argument("new_name")
def clone_basket(basket_id: int, new_name: str):
    """Clone an existing basket."""
    with db_session() as db:
        try:
            logger.info(f"Cloning basket {basket_id} to {new_name}")
            service = BasketService(db)
            clone = service.clone_basket(basket_id, new_name)
            click.echo(
                f"\nCloned basket:"
                f"\nOriginal ID: {basket_id}"
                f"\nNew ID: {clone.id}"
                f"\nNew Name: {clone.name}"
            )
        except Exception as e:
            logger.error(f"Error cloning basket: {str(e)}", exc_info=True)
            ErrorService(db).log_error("ERROR", "CLI", str(e))
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
@click.argument("basket_id", type=int)
def calculate_inflation(basket_id: int):
    """Calculate inflation for a basket."""
    with db_session() as db:
        try:
            logger.info(f"Calculating inflation for basket {basket_id}")
            service = InflationService(db)
            inflation, calculated_at = service.calculate_basket_inflation(basket_id)
            
            # Get the basket name
            basket = db.query(Basket).get(basket_id)
            if not basket:
                click.echo(f"Error: Basket {basket_id} not found", err=True)
                return
            
            # Get the inflation index
            index = (
                db.query(InflationIndex)
                .filter(InflationIndex.basket_id == basket_id)
                .first()
            )
            
            if not index:
                click.echo(f"Error: No inflation data found for basket {basket_id}", err=True)
                return
            
            # Display results
            click.echo(f"\nInflation Report for Basket: {basket.name}")
            click.echo(f"Calculated At: {calculated_at}")
            click.echo("\nOverall Basket:")
            click.echo(f"Base Index: {index.base_index:.1f} (at {index.base_date})")
            click.echo(f"Current Index: {index.current_index:.1f}")
            click.echo(f"Change: {inflation:+.1f}%")
            
        except Exception as e:
            logger.error(f"Error calculating inflation: {str(e)}", exc_info=True)
            ErrorService(db).log_error("ERROR", "CLI", str(e))
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
def init():
    """Initialize the database."""
    try:
        logger.info("Initializing database")
        init_db()
        click.echo("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        click.echo(f"Error initializing database: {str(e)}", err=True)


if __name__ == "__main__":
    cli()
