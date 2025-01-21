"""Command-line interface for the application."""
import click
from sqlalchemy.orm import Session

from basketcase.api import KrogerAPI
from basketcase.database import db_session, init_db
from basketcase.models import Basket, Category, InflationIndex
from basketcase.services import (BasketService, ErrorService, InflationService,
                               ProductService, StoreService)


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
            service = StoreService(db, KrogerAPI())
            stores = service.find_nearby_stores(postal_code)
            
            click.echo("\nNearby Stores:")
            for store in stores:
                click.echo(
                    f"\n{store.name}"
                    f"\n{store.address}"
                    f"\n{store.postal_code}"
                )
        except Exception as e:
            ErrorService(db).log_error("ERROR", "CLI", str(e))
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
@click.argument("term")
@click.argument("store_id")
def search_products(term: str, store_id: str):
    """Search for products at a store."""
    with db_session() as db:
        try:
            service = ProductService(db, KrogerAPI())
            products = service.search_products(term, store_id)
            
            click.echo("\nProducts Found:")
            for product in products:
                click.echo(
                    f"\n{product.name}"
                    f"\nID: {product.product_id}"
                    f"\nUPC: {product.upc or 'N/A'}"
                    f"\nBrand: {product.brand or 'N/A'}"
                    f"\nSize: {product.size or 'N/A'}"
                )
        except Exception as e:
            ErrorService(db).log_error("ERROR", "CLI", str(e))
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
@click.argument("name")
@click.argument("store_id")
def create_basket(name: str, store_id: str):
    """Create a new basket."""
    with db_session() as db:
        try:
            service = BasketService(db)
            basket = service.create_basket(name, store_id)
            click.echo(f"\nCreated basket: {basket.name} (ID: {basket.id})")
        except Exception as e:
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
            service = BasketService(db)
            item = service.add_to_basket(basket_id, product_id, quantity)
            click.echo(
                f"\nAdded to basket:"
                f"\nProduct ID: {item.product_id}"
                f"\nQuantity: {item.quantity}"
            )
        except Exception as e:
            ErrorService(db).log_error("ERROR", "CLI", str(e))
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
@click.argument("basket_id", type=int)
@click.argument("new_name")
def clone_basket(basket_id: int, new_name: str):
    """Clone an existing basket."""
    with db_session() as db:
        try:
            service = BasketService(db)
            clone = service.clone_basket(basket_id, new_name)
            click.echo(
                f"\nCloned basket:"
                f"\nOriginal ID: {basket_id}"
                f"\nNew ID: {clone.id}"
                f"\nNew Name: {clone.name}"
            )
        except Exception as e:
            ErrorService(db).log_error("ERROR", "CLI", str(e))
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
@click.argument("basket_id", type=int)
def calculate_inflation(basket_id: int):
    """Calculate inflation for a basket."""
    with db_session() as db:
        try:
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
            ErrorService(db).log_error("ERROR", "CLI", str(e))
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
def init():
    """Initialize the database."""
    try:
        init_db()
        click.echo("Database initialized successfully.")
    except Exception as e:
        click.echo(f"Error initializing database: {str(e)}", err=True)


if __name__ == "__main__":
    cli()
