# basketcase
Track a basket of grocery products over time to build a real inflation index for your area

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/basketcase.git
cd basketcase
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

4. Copy env_template to .env and update with your Kroger API credentials:
```bash
copy env_template .env
```

5. Initialize the database:
```bash
basketcase init
```

## Usage

### Find Nearby Stores
```bash
basketcase find-stores [postal_code]
```

### Search for Products
```bash
basketcase search-products [search_term] [store_id]
```

### Create a Basket
```bash
basketcase create-basket [basket_name] [store_id]
```

### Add Items to Basket
```bash
basketcase add-to-basket [basket_id] [product_id] [quantity]
```

### Clone a Basket
```bash
basketcase clone-basket [basket_id] [new_name]
```

### Calculate Inflation
```bash
basketcase calculate-inflation [basket_id]
```

### Install Price Update Service
To install the price update service that runs weekly:
```bash
python scripts/run_scheduler.py install
```

To start the service:
```bash
python scripts/run_scheduler.py start
```

To stop the service:
```bash
python scripts/run_scheduler.py stop
```

To remove the service:
```bash
python scripts/run_scheduler.py remove
```

## Features

- Find nearby Kroger stores by postal code
- Search for products by name
- Create and manage shopping baskets (up to 50 items)
- Track price changes over time
- Calculate category-specific inflation rates
- Clone and modify baskets
- Weekly price updates

## Development

1. Install development dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest
```

## License

MIT License
