"""Kroger API client implementation."""
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from requests.exceptions import RequestException

from basketcase.config import (KROGER_BASE_URL, KROGER_CLIENT_ID,
                             KROGER_CLIENT_SECRET)

# Set up logging
logger = logging.getLogger(__name__)

class KrogerAPI:
    """Simple client for the Kroger API."""

    def __init__(self) -> None:
        """Initialize the API client."""
        self.base_url = KROGER_BASE_URL
        self.client_id = KROGER_CLIENT_ID
        self.client_secret = KROGER_CLIENT_SECRET
        if not self.client_id or not self.client_secret:
            logger.error("Missing Kroger API credentials")
            raise ValueError("KROGER_CLIENT_ID and KROGER_CLIENT_SECRET must be set")
            
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        logger.info(f"Initialized KrogerAPI with base_url={self.base_url}")

    def get_token(self) -> str:
        """Get a valid access token."""
        if self.token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            logger.debug("Using cached token")
            return self.token

        auth_url = urljoin(self.base_url, "connect/oauth2/token")
        # Create base64 encoded auth string
        auth_string = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_string}"
        }
        data = {
            "grant_type": "client_credentials",
            "scope": "product.compact"
        }

        try:
            logger.info(f"Getting new token from {auth_url}")
            response = requests.post(auth_url, headers=headers, data=data)
            logger.debug(f"Token response status: {response.status_code}")
            logger.debug(f"Token response headers: {response.headers}")
            if response.status_code != 200:
                logger.error(f"Token response error: {response.text}")
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data["access_token"]
            self.token_expiry = datetime.utcnow() + timedelta(
                seconds=token_data["expires_in"] - 60
            )
            logger.info("Successfully obtained new token")
            return self.token
        except RequestException as e:
            logger.error(f"Failed to get token: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get access token: {str(e)}") from e

    def _make_request(
        self, method: str, endpoint: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Kroger API."""
        url = urljoin(self.base_url, endpoint)
        headers = {"Authorization": f"Bearer {self.get_token()}"}

        try:
            logger.info(f"Making {method} request to {url}")
            logger.debug(f"Request params: {params}")
            response = requests.request(method, url, headers=headers, params=params)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            if response.status_code != 200:
                logger.error(f"Response error: {response.text}")
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"API request failed: {str(e)}", exc_info=True)
            raise Exception(f"API request failed: {str(e)}") from e

    def find_stores(self, zip_code: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find stores near a zip code.
        
        Args:
            zip_code: 5-digit zip code
            limit: Maximum number of stores to return (default: 10, max: 200)
        """
        params = {
            "filter.zipCode.near": zip_code,
            "filter.limit": min(limit, 200)  # API max limit is 200
        }
        logger.info(f"Finding stores near {zip_code}")
        response = self._make_request("GET", "locations", params)
        stores = response.get("data", [])
        logger.debug(f"Found {len(stores)} stores")
        return stores

    def search_products(
        self, term: str, location_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for products at a specific location.
        
        Args:
            term: Search term (min 3 characters, max 8 words)
            location_id: 8-character store ID
            limit: Maximum number of products to return (default: 10)
        """
        if len(term) < 3:
            raise ValueError("Search term must be at least 3 characters")
        if len(location_id) != 8:
            raise ValueError("Location ID must be 8 characters")
            
        params = {
            "filter.term": term,
            "filter.locationId": location_id,
            "filter.limit": limit
        }
        logger.info(f"Searching for '{term}' at location {location_id}")
        response = self._make_request("GET", "products", params)
        products = response.get("data", [])
        logger.debug(f"Found {len(products)} products")
        return products

    def get_product_prices(
        self, product_ids: List[str], store_id: str
    ) -> Dict[str, float]:
        """Get current prices for products at a store.
        
        Args:
            product_ids: List of product IDs
            store_id: 8-character store ID
        """
        if len(store_id) != 8:
            raise ValueError("Store ID must be 8 characters")
            
        prices = {}
        for product_id in product_ids:
            logger.info(f"Getting price for product {product_id} at store {store_id}")
            response = self._make_request(
                "GET",
                f"products/{product_id}",
                params={"filter.locationId": store_id}
            )
            
            if "data" in response:
                items = response["data"]
                if items and items[0].get("items"):
                    price_info = items[0]["items"][0].get("price", {})
                    regular_price = price_info.get("regular")
                    if regular_price:
                        prices[product_id] = float(regular_price)
                        logger.debug(f"Price for {product_id}: {prices[product_id]}")
                    else:
                        logger.warning(f"No regular price found for {product_id}")
                else:
                    logger.warning(f"No items found for {product_id}")
            else:
                logger.warning(f"No data found for {product_id}")
                
        return prices
