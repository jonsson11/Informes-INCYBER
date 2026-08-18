import requests
from datetime import datetime
from api.bitdefender import HEADERS
from config import API_HOST

def fetch_quarantine_items(company_id: str, start_date=None, end_date=None) -> list:
    """
    Devuelve el inventario de elementos en cuarentena para una empresa,
    filtrado estrictamente por el rango de fechas proporcionado (start_date y end_date).
    """
    url = f"{API_HOST}/quarantine/computers"
    items = []
    page = 1
    per_page = 30

    while True:
        body = {
            "jsonrpc": "2.0",
            "method": "getQuarantineItemsList",
            "params": {
                "companyId": company_id,
                "page": page,
                "perPage": per_page,
            },
            "id": "incyber",
        }

        r = requests.post(url, headers=HEADERS, json=body)
        r.raise_for_status()
        data = r.json()

        if "error" in data:
            print(f"      [!] Error al consultar Quarantine API: {data['error']}")
            return items

        result = data.get("result", {})
        page_items = result.get("items", [])
        items.extend(page_items)

        pages_count = result.get("pagesCount", 1)
        if page >= pages_count or not page_items:
            break
        page += 1

    quarantine_table_rows = []
    for item in items:
        # El campo correcto de la fecha según tu archivo es 'quarantinedOn'
        raw_date = item.get("quarantinedOn", "")
        
        keep_item = True
        
        if raw_date and (start_date or end_date):
            try:
                # Extraemos los primeros 10 caracteres (YYYY-MM-DD) para evitar problemas de formato de hora
                date_part = raw_date[:10]
                item_dt = datetime.strptime(date_part, "%Y-%m-%d").date()
                
                # Comparamos contra el rango del mes
                if start_date and item_dt < start_date:
                    keep_item = False
                if end_date and item_dt > end_date:
                    keep_item = False
            except Exception as e:
                print(f"      [!] No se pudo procesar la fecha de cuarentena '{raw_date}': {e}")
                keep_item = False # Por seguridad, si la fecha es corrupta o vieja, no la incluimos

        if keep_item:
            quarantine_table_rows.append({
                "Endpoint": item.get("endpointName", ""),
                "Malware": item.get("threatName", ""),
                "Fecha": raw_date,
                "Ruta": item.get("details", {}).get("filePath", ""),
            })

    return quarantine_table_rows