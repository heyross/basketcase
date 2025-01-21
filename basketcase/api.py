"""Kroger API client implementation."""
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from requests.exceptions import RequestException

from basketcase.config import KROGER_BASE_URL, KROGER_CLIENT_ID


class KrogerAPI:
    """Simple client for the Kroger API."""

    def __init__(self) -> None:
        """Initialize the API client."""
        self.base_url = KROGER_BASE_URL
        self.client_id = KROGER_CLIENT_ID
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

    def get_token(self) -> str:
        """Get a valid access token."""
        if self.token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            return self.token

        auth_url = urljoin(self.base_url, "connect/oauth2/token")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self.client_id}"
        }
        data = {"grant_type": "client_credentials", "scope": "product.compact"}

        try:
            response = requests.post(auth_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data["access_token"]
            self.token_expiry = datetime.utcnow() + timedelta(
                seconds=token_data["expires_in"] - 60
            )
            return self.token
        except RequestException as e:
            raise Exception(f"Failed to get access token: {str(e)}") from e

    def _make_request(
        self, method: str, endpoint: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Kroger API."""
        url = urljoin(self.base_url, endpoint)
        headers = {"Authorization": f"Bearer {self.get_token()}"}

        try:
            response = requests.request(method, url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"API request failed: {str(e)}") from e

    def find_stores(self, zip_code: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find stores near a zip code."""
        params = {
            "filter.zipCode.near": zip_code,
            "filter.limit": limit
        }
        response = self._make_request("GET", "locations", params)
        return response.get("data", [])

    def search_products(
        self, term: str, location_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for products at a specific location."""
        params = {
            "filter.term": term,
            "filter.locationId": location_id,
            "filter.limit": limit
        }
        response = self._make_request("GET", "products", params)
        return response.get("data", [])

    def get_product_prices(
        self, product_ids: List[str], store_id: str
    ) -> Dict[str, float]:
        """Get current prices for products at a store."""
        prices = {}
        for product_id in product_ids:
            data = self._make_request(
                "GET",
                f"{self.base_url}/products/{product_id}",
                params={"locationId": store_id}
            )
            if "data" in data and data["data"] and data["data"][0]["items"]:
                prices[product_id] = float(data["data"][0]["items"][0]["price"]["regular"])
        return prices
