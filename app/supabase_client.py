"""Direct Supabase REST client for Farmzy backend (No direct PostgreSQL URI or passwords required)."""
import httpx
from typing import Dict, List, Optional, Any
from app.config import settings


class SupabaseClient:
    """Supabase REST API client using PostgREST."""

    def __init__(self):
        self.url = (settings.supabase_url or "").rstrip("/")
        self.key = settings.supabase_key or ""
        self.rest_url = f"{self.url}/rest/v1" if self.url else ""

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.key)

    def _headers(self, return_rep: bool = True) -> Dict[str, str]:
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if return_rep:
            headers["Prefer"] = "return=representation"
        return headers

    def select(
        self,
        table: str,
        params: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
    ) -> List[Dict[str, Any]]:
        """Query rows from a table."""
        if not self.is_configured:
            return []
        
        endpoint = f"{self.rest_url}/{table}"
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(endpoint, headers=self._headers(return_rep=False), params=params)
                if resp.status_code == 200:
                    return resp.json()
                print(f"[Supabase select error] {table}: {resp.status_code} {resp.text}")
                return []
        except Exception as e:
            print(f"[Supabase select exception] {table}: {e}")
            return []

    def insert(
        self,
        table: str,
        data: Dict[str, Any] | List[Dict[str, Any]],
        timeout: float = 10.0,
    ) -> Optional[Any]:
        """Insert a row or multiple rows into a table."""
        if not self.is_configured:
            return None
        
        endpoint = f"{self.rest_url}/{table}"
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(endpoint, headers=self._headers(return_rep=True), json=data)
                if resp.status_code in (200, 201):
                    result = resp.json()
                    return result[0] if isinstance(result, list) and len(result) > 0 else result
                print(f"[Supabase insert error] {table}: {resp.status_code} {resp.text}")
                return None
        except Exception as e:
            print(f"[Supabase insert exception] {table}: {e}")
            return None

    def update(
        self,
        table: str,
        data: Dict[str, Any],
        match_params: Dict[str, str],
        timeout: float = 10.0,
    ) -> Optional[Any]:
        """Update rows in a table."""
        if not self.is_configured:
            return None
        
        endpoint = f"{self.rest_url}/{table}"
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.patch(endpoint, headers=self._headers(return_rep=True), params=match_params, json=data)
                if resp.status_code in (200, 204):
                    return resp.json() if resp.status_code == 200 else data
                print(f"[Supabase update error] {table}: {resp.status_code} {resp.text}")
                return None
        except Exception as e:
            print(f"[Supabase update exception] {table}: {e}")
            return None

    # --- Domain Specific Helpers ---

    # Listings
    def get_listings(self, farm_id: Optional[str] = None, status: Optional[str] = "active", limit: int = 100) -> List[Dict[str, Any]]:
        params = {"order": "created_at.desc", "limit": str(limit)}
        if farm_id:
            params["farm_id"] = f"eq.{farm_id}"
        if status:
            params["status"] = f"eq.{status}"
        return self.select("listings", params)

    def create_listing(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.insert("listings", data)

    # Orders
    def get_orders(self, farm_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        params = {"order": "created_at.desc", "limit": str(limit)}
        if farm_id:
            params["farm_id"] = f"eq.{farm_id}"
        return self.select("orders", params)

    def create_order(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.insert("orders", data)

    # Soil Readings
    def get_soil_readings(self, device_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        params = {"order": "timestamp.desc", "limit": str(limit)}
        if device_id:
            params["device_id"] = f"eq.{device_id}"
        return self.select("soil_readings", params)

    def create_soil_reading(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.insert("soil_readings", data)

    # Soil Health
    def get_latest_soil_health(self, device_id: Optional[str] = None, farm_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        params = {"order": "date.desc", "limit": "1"}
        if device_id:
            params["device_id"] = f"eq.{device_id}"
        if farm_id:
            params["farm_id"] = f"eq.{farm_id}"
        records = self.select("soil_health", params)
        return records[0] if records else None

    def get_soil_health_history(self, device_id: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        params = {"order": "date.desc", "limit": str(limit)}
        if device_id:
            params["device_id"] = f"eq.{device_id}"
        return self.select("soil_health", params)

    def create_soil_health(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.insert("soil_health", data)

    # Recommendations
    def get_latest_recommendation(self, device_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        params = {"order": "created_at.desc", "limit": "1"}
        if device_id:
            params["device_id"] = f"eq.{device_id}"
        records = self.select("recommendations", params)
        return records[0] if records else None

    def create_recommendation(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.insert("recommendations", data)

    # Irrigation Plans
    def get_irrigation_plans(self, farm_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        params = {"order": "created_at.desc", "limit": str(limit)}
        if farm_id:
            params["farm_id"] = f"eq.{farm_id}"
        return self.select("irrigation_plans", params)

    def create_irrigation_plan(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.insert("irrigation_plans", data)

    # Routes & Deliveries
    def get_routes(self, limit: int = 10) -> List[Dict[str, Any]]:
        params = {"order": "created_at.desc", "limit": str(limit)}
        return self.select("routes", params)

    def create_route(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.insert("routes", data)

    def get_deliveries(self, farm_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        params = {"order": "created_at.desc", "limit": str(limit)}
        if farm_id:
            params["farm_id"] = f"eq.{farm_id}"
        return self.select("deliveries", params)

    def create_delivery(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.insert("deliveries", data)


supabase = SupabaseClient()
