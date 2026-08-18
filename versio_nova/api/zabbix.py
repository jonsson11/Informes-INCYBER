import requests

from config import ZABBIX_API_HOST, ZABBIX_API_TOKEN

HEADERS = {
    "Content-Type": "application/json-rpc",
    "Authorization": f"Bearer {ZABBIX_API_TOKEN}",
}


def api_call(method: str, params: dict = None) -> dict:
    """
    Llama a la API JSON-RPC de Zabbix (api_jsonrpc.php).
    Desde Zabbix 6.4+ el token va en el header Authorization,
    así que no hace falta login/logout ni pasar 'auth' en el body.
    """
    resp = requests.post(
        ZABBIX_API_HOST,
        headers=HEADERS,
        json={
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1,
        },
    )
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"Zabbix API error en '{method}': {data['error']}")

    return data