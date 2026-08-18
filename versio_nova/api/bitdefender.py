import base64
import requests
from config import API_KEY, API_HOST

_b64 = base64.b64encode(f"{API_KEY}:".encode()).decode()

HEADERS = {"Authorization": f"Basic {_b64}","Content-Type": "application/json",}


def api_call(service_method: str, params: dict = None) -> dict:
    service, method = service_method.split(".", 1)
    resp = requests.post(f"{API_HOST}/{service}",headers=HEADERS,json={
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": "incyber",
        },
    )
    resp.raise_for_status()
    return resp.json()