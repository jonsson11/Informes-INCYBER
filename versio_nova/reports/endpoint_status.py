import io
import time
import zipfile

import pandas as pd
import requests

from datetime import datetime
from dateutil.relativedelta import relativedelta

from config import REPORT_TYPE_ENDPOINT_PROTECTION_STATUS
from api.bitdefender import api_call, HEADERS


def fetch_endpoint_protection_status(cid: str) -> dict:
    """
    Crea un informe instantáneo Endpoint Protection Status y devuelve un
    resumen {"online": N, "offline": N, "total": N} a partir del CSV.
    Este es el informe correcto para saber qué endpoints están realmente
    activos/online (filterType=0 = todos los endpoints, sin filtros extra).
    """

    params_report = {
        "type": REPORT_TYPE_ENDPOINT_PROTECTION_STATUS,
        "name": f"INCYBER_EndpointStatus_{int(time.time())}",
        "targetIds": [cid],
        "options": {"filterType": 0},
    }

    r_create = api_call("reports.createReport", params_report)
    report_id = r_create.get("result")

    if not report_id:
        print(
            f"      [!] No se pudo crear el informe de estado: "
            f"{r_create.get('error')}"
        )
        return {}

    url_csv = None

    for _ in range(10):
        time.sleep(3)

        r_links = api_call("reports.getDownloadLinks",{"reportId": report_id})
        if "error" in r_links:
            print(f"      [!] Error consultando getDownloadLinks: {r_links['error']}")
            time.sleep(3)
            continue
        result = r_links.get("result", {})
        if result.get("readyForDownload"):
            url_csv = result.get("lastInstanceUrl")
            break

    if not url_csv:
        print("      [!] El informe de estado no estuvo listo a tiempo.")
        return {}

    z_bytes = None
    last_debug = ""
    for attempt in range(4):
        r_file = requests.get(url_csv, headers=HEADERS)
        content = r_file.content
        if r_file.status_code == 200 and content[:2] == b"PK":
            z_bytes = content
            break
        last_debug = (
            f"status={r_file.status_code} "
            f"content-type={r_file.headers.get('Content-Type')} "
            f"len={len(content)} "
            f"body_start={content[:200]!r}"
        )
        time.sleep(3)

    if z_bytes is None:
        print("      [!] La descarga del informe de estado no es un ZIP válido tras varios intentos.")
        print(f"      [debug] {last_debug}")
        return {}

    with zipfile.ZipFile(io.BytesIO(z_bytes)) as z:
        csv_name = next(
            (n for n in z.namelist() if n.endswith(".csv")),
            None
        )

        if not csv_name:
            return {}
        content = z.read(csv_name).decode("utf-8",errors="ignore")

    sep = ";" if ";" in content.splitlines()[0] else ","
    df = pd.read_csv(io.StringIO(content),sep=sep,on_bad_lines="skip")
    df.columns = [c.strip() for c in df.columns]
    online_col = next((c for c in df.columns if c.strip().lower() == "online"),None)
    last_update_col = next((c for c in df.columns if c.strip().lower() in ("last update", "last seen")),)

    if not online_col and not last_update_col:
        print(
            "      [!] No se encontraron columnas "
            "'Online' ni 'Last Update'/'Last Seen'. "
            f"Columnas disponibles: {list(df.columns)}"
        )
        return {}

    if online_col:
        online_vals = (df[online_col].astype(str).str.strip().str.lower())
        is_online = online_vals.isin({"online", "yes", "true", "1"})
    else:
        is_online = pd.Series(False, index=df.index)

    if last_update_col:
        cutoff = datetime.now() - relativedelta(days=30)
        raw = (df[last_update_col].astype(str).str.strip())
        last_seen_dt = pd.to_datetime( raw, errors="coerce", dayfirst=True)
        is_recent = (last_seen_dt.notna() & (last_seen_dt >= cutoff)
        )
    else:
        is_recent = pd.Series(False, index=df.index)

    is_active = is_online | is_recent
    online = int(is_active.sum())
    offline = int(len(df) - online)

    return {"online": online,"offline": offline,"total": len(df),}