# Inflation Calculation Analysis

## Overview
This document analyzes the complete flow of inflation calculation in the basketcase application, from CLI to database, identifying all dependencies, data flows, and potential issues.

## 1. Entry Points

### 1.1 CLI Entry (`cli.py`)
```python
@cli.command()
@click.argument("basket_id", type=int)
def calculate_inflation(basket_id: int):
```
- **Input**: basket_id from command line
- **Process**: 
  1. Creates InflationService instance
  2. Calls calculate_basket_inflation()
  3. Formats and displays results
- **Output**: Displays inflation report to console
- **Dependencies**: InflationService, db_session

### 1.2 Scheduler Entry (`scheduler.py`)
```python
def update_prices(self):
```
- **Input**: None (uses internal API client)
- **Process**:
  1. Gets active products
  2. Fetches current prices from Kroger API
  3. Updates price history
- **Output**: Updates PriceHistory table
- **Dependencies**: KrogerAPI, db_session

## 2. Core Services

### 2.1 InflationService (`services.py`)
```python
def calculate_basket_inflation(self, basket_id: int) -> Tuple[float, datetime]:
```
- **Input**: basket_id
- **Process**:
  1. Retrieves basket and items
  2. Gets historical prices
  3. Calculates inflation
  4. Updates inflation index
- **Output**: (inflation_percentage, calculation_time)
- **Dependencies**: Basket, BasketItem, PriceHistory, InflationIndex models

## 3. Data Flow Analysis

### 3.1 Price Data Flow
1. **Source**: Kroger API via scheduler
2. **Storage**: PriceHistory table
3. **Usage**: InflationService for calculations
4. **Issues Identified**:
   - No validation of price data consistency
   - No handling of missing historical prices
   - No date range constraints on price queries

### 3.2 Basket Data Flow
1. **Source**: User input via CLI
2. **Storage**: Basket and BasketItem tables
3. **Usage**: InflationService for calculations
4. **Issues Identified**:
   - No validation of basket item quantities
   - No handling of empty baskets
   - No category weighting in calculations

### 3.3 Index Data Flow
1. **Source**: InflationService calculations
2. **Storage**: InflationIndex table
3. **Usage**: CLI display
4. **Issues Identified**:
   - Inconsistent base date handling
   - No validation of index values
   - No historical index tracking

## 4. Identified Problems

### 4.1 Data Integrity Issues
1. **Base Price Selection**
   - Current: Uses first available price
   - Problem: May not correspond to basket creation date
   - Impact: Incorrect inflation calculations

2. **Current Price Selection**
   - Current: Uses latest price
   - Problem: No date range validation
   - Impact: May use outdated prices

3. **Empty Basket Handling**
   - Current: Raises error
   - Problem: Inconsistent with CLI expectations
   - Impact: CLI test failures

### 4.2 Calculation Issues
1. **Inflation Percentage**
   - Current: Simple percentage calculation
   - Problem: Doesn't handle weighted averages
   - Impact: Inaccurate basket inflation

2. **Index Values**
   - Current: Direct conversion from percentage
   - Problem: No validation or rounding
   - Impact: Display inconsistencies

### 4.3 Test Data Issues
1. **Fixture Setup**
   - Current: Incomplete test data
   - Problem: Missing required relationships
   - Impact: Test failures

2. **Mock API**
   - Current: Inconsistent mock data
   - Problem: Doesn't match production format
   - Impact: Scheduler test failures

## 5. Required Fixes

### 5.1 Data Layer
1. Update PriceHistory queries to:
   - Use basket creation date for base price
   - Implement date range constraints
   - Handle missing price data

2. Update InflationIndex to:
   - Store historical calculations
   - Validate index values
   - Track calculation metadata

### 5.2 Service Layer
1. Update InflationService to:
   - Implement weighted average calculations
   - Handle empty baskets gracefully
   - Validate price data consistency

2. Update PriceUpdateScheduler to:
   - Validate API responses
   - Handle partial updates
   - Implement retry logic

### 5.3 Presentation Layer
1. Update CLI to:
   - Handle calculation errors gracefully
   - Format numbers consistently
   - Provide detailed error messages

### 5.4 Test Suite
1. Update test fixtures to:
   - Provide complete test data
   - Match production data structures
   - Cover edge cases

2. Update mock objects to:
   - Match API response format
   - Simulate real-world scenarios
   - Test error conditions

## 6. Implementation Priority
1. Fix data integrity issues (base price selection, current price validation)
2. Implement proper weighted calculations
3. Update test fixtures and mocks
4. Enhance error handling and validation
5. Improve CLI output formatting

## 7. Dependencies to Update
- Models: Basket, PriceHistory, InflationIndex
- Services: InflationService, PriceUpdateScheduler
- Tests: test_services.py, test_cli.py, test_scheduler.py
- CLI: calculate_inflation command
