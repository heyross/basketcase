"""Database models for the application."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (Boolean, DateTime, Enum, Float, ForeignKey, Integer,
                       String, Text)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Store(Base):
    """Store model representing a Kroger store location."""
    __tablename__ = "stores"

    store_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    postal_code: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    hours: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    baskets = relationship("Basket", back_populates="store")
    price_history = relationship("PriceHistory", back_populates="store")


class Category(Base):
    """Category model for product categorization."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    products = relationship("Product", back_populates="category")
    parent = relationship("Category", remote_side=[id], backref="children")


class Product(Base):
    """Product model representing a Kroger product."""
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String, primary_key=True)
    upc: Mapped[Optional[str]] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    description: Mapped[Optional[str]] = mapped_column(Text)
    size: Mapped[Optional[str]] = mapped_column(String)
    image_url: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    category = relationship("Category", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product")
    basket_items = relationship("BasketItem", back_populates="product")


class Basket(Base):
    """Basket model for grouping products."""
    __tablename__ = "baskets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.store_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_basket_id: Mapped[Optional[int]] = mapped_column(ForeignKey("baskets.id"))

    # Relationships
    store = relationship("Store", back_populates="baskets")
    items = relationship("BasketItem", back_populates="basket")
    parent = relationship("Basket", remote_side=[id], backref="children")
    inflation_indices = relationship("InflationIndex", back_populates="basket")


class BasketItem(Base):
    """Association model between Basket and Product."""
    __tablename__ = "basket_items"

    basket_id: Mapped[int] = mapped_column(
        ForeignKey("baskets.id"), primary_key=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.product_id"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    added_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    basket = relationship("Basket", back_populates="items")
    product = relationship("Product", back_populates="basket_items")


class PriceHistory(Base):
    """Price history model for tracking product prices."""
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.product_id"), nullable=False
    )
    store_id: Mapped[str] = mapped_column(
        ForeignKey("stores.store_id"), nullable=False
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    promo_price: Mapped[Optional[float]] = mapped_column(Float)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    product = relationship("Product", back_populates="price_history")
    store = relationship("Store", back_populates="price_history")


class InflationIndex(Base):
    """Inflation index model for tracking price changes."""
    __tablename__ = "inflation_indices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    basket_id: Mapped[int] = mapped_column(ForeignKey("baskets.id"), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    base_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_index: Mapped[float] = mapped_column(Float, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    basket = relationship("Basket", back_populates="inflation_indices")
    category = relationship("Category")


class ErrorLog(Base):
    """Error log model for tracking application errors."""
    __tablename__ = "error_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    level: Mapped[str] = mapped_column(String, nullable=False)  # ERROR, WARNING, INFO
    component: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
