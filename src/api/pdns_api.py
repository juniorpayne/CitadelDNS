import requests
from fastapi import HTTPException
from ..config.settings import PDNS_API_URL, PDNS_API_KEY

class PowerDNSAPI:
    def __init__(self):
        self.api_url = PDNS_API_URL
        self.api_key = PDNS_API_KEY
        self.headers = {"X-API-Key": self.api_key}

    def notify_zone_change(self, zone_name: str) -> None:
        """Notify PowerDNS of a zone change."""
        try:
            response = requests.put(
                f"{self.api_url}/servers/localhost/zones/{zone_name}",
                headers=self.headers,
                json={"serial": 0}  # Force serial update
            )

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=500,
                    detail=f"PowerDNS API error: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"PowerDNS API error: {str(e)}"
            )