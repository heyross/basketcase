# Database Architecture

## Overview
The application uses SQLite for local data storage, focusing on efficient price tracking and basket management. The schema is designed to support the core features while maintaining data integrity and performance.

## Tables

### stores
```sql
CREATE TABLE stores (
    store_id TEXT PRIMARY KEY,      -- Kroger store ID
    name TEXT NOT NULL,             -- Store name
    address TEXT NOT NULL,          -- Full address
    postal_code TEXT NOT NULL,      -- Store postal code
    latitude REAL NOT NULL,         -- Store latitude
    longitude REAL NOT NULL,        -- Store longitude
    hours TEXT,                     -- Operating hours as JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stores_postal_code ON stores(postal_code);
```

### products
```sql
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,    -- Kroger product ID
    upc TEXT UNIQUE,               -- UPC code (if available)
    name TEXT NOT NULL,            -- Product name
    brand TEXT,                    -- Brand name
    category_id INTEGER,           -- Foreign key to categories
    description TEXT,              -- Product description
    size TEXT,                     -- Package size
    image_url TEXT,               -- Product image URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_upc ON products(upc);
```

### categories
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,      -- Category name
    parent_id INTEGER,              -- For hierarchical categories
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

CREATE INDEX idx_categories_parent ON categories(parent_id);
```

### baskets
```sql
CREATE TABLE baskets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,             -- Basket name
    store_id TEXT NOT NULL,         -- Associated store
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_template BOOLEAN DEFAULT FALSE,  -- True if this is a template basket
    parent_basket_id INTEGER,       -- ID of the original basket if cloned
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (parent_basket_id) REFERENCES baskets(id)
);

CREATE INDEX idx_baskets_store ON baskets(store_id);
CREATE INDEX idx_baskets_parent ON baskets(parent_basket_id);
```

### basket_items
```sql
CREATE TABLE basket_items (
    basket_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (basket_id, product_id),
    FOREIGN KEY (basket_id) REFERENCES baskets(id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX idx_basket_items_product ON basket_items(product_id);
```

### price_history
```sql
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    store_id TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    promo_price DECIMAL(10,2),      -- Promotional price if available
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

CREATE INDEX idx_price_history_product ON price_history(product_id);
CREATE INDEX idx_price_history_store ON price_history(store_id);
CREATE INDEX idx_price_history_captured ON price_history(captured_at);
```

### inflation_indices
```sql
CREATE TABLE inflation_indices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    basket_id INTEGER NOT NULL,
    category_id INTEGER,           -- NULL for overall basket index
    base_date DATE NOT NULL,       -- Date when index = 100
    current_index DECIMAL(10,2) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (basket_id) REFERENCES baskets(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE INDEX idx_inflation_indices_basket ON inflation_indices(basket_id);
CREATE INDEX idx_inflation_indices_category ON inflation_indices(category_id);
```

### error_logs
```sql
CREATE TABLE error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level TEXT NOT NULL,           -- ERROR, WARNING, INFO
    component TEXT NOT NULL,       -- System component (API, Database, Scheduler, etc.)
    message TEXT NOT NULL,         -- Error message
    details TEXT,                  -- Additional error details (stack trace, context)
    resolved BOOLEAN DEFAULT FALSE -- Whether the error has been addressed
);

CREATE INDEX idx_error_logs_timestamp ON error_logs(timestamp);
CREATE INDEX idx_error_logs_level ON error_logs(level);
CREATE INDEX idx_error_logs_component ON error_logs(component);
CREATE INDEX idx_error_logs_resolved ON error_logs(resolved);
```

## Key Design Considerations

1. **Data Integrity**
   - Foreign key constraints ensure referential integrity
   - Timestamps track creation and updates
   - Indices optimize common queries

2. **Price History**
   - Separate table for historical prices enables efficient time-series analysis
   - Captures both regular and promotional prices
   - Store-specific pricing

3. **Basket Management**
   - Supports basket cloning through parent_basket_id
   - Template baskets for reuse
   - Many-to-many relationship between baskets and products

4. **Category Hierarchy**
   - Self-referential categories table supports nested categories
   - Flexible categorization system

5. **Inflation Tracking**
   - Separate indices table for efficient inflation calculations
   - Supports both overall and category-specific indices
   - Maintains historical base dates

## Performance Considerations

1. **Indexing Strategy**
   - Indices on frequently queried columns
   - Composite indices for common join operations
   - Balance between query performance and write overhead

2. **Data Archival**
   - Price history table may grow large over time
   - Consider implementing partitioning or archival strategy

3. **Query Optimization**
   - Denormalized category paths for faster hierarchy traversal
   - Precalculated indices for common time periods
