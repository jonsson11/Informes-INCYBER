import io
import time

import pandas as pd

from datetime import datetime
from dateutil.relativedelta import relativedelta

from config import REPORT_TYPE_ENDPOINT_PROTECTION_STATUS
from api.reports_batch import extract_csv_from_zip


def build_endpoint_status_report_params(cid: str) -> dict:
    """Parametros para crear el informe Endpoint Protection Status (sin crearlo ni esperar)."""
    return {
        "type": REPORT_TYPE_ENDPOINT_PROTECTION_STATUS,
        "name": f"INCYBER_EndpointStatus_{int(time.time())}",
        "targetIds": [cid],
        "options": {"filterType": 0},
    }


def parse_endpoint_status_zip(z_bytes: bytes) -> dict:
    """
    A partir del ZIP ya descargado del informe Endpoint Protection Status,
    devuelve un resumen {"online": N, "offline": N, "total": N}.
    """
    content = extract_csv_from_zip(z_bytes)
    if not content:
        return {}

    sep = ";" if ";" in content.splitlines()[0] else ","
    df = pd.read_csv(io.StringIO(content), sep=sep, on_bad_lines="skip")
    df.columns = [c.strip() for c in df.columns]
    online_col = next((c for c in df.columns if c.strip().lower() == "online"), None)
    last_update_col = next((c for c in df.columns if c.strip().lower() in ("last update", "last seen")), None)

    if not online_col and not last_update_col:
        print(
            "      [!] No se encontraron columnas "
            "'Online' ni 'Last Update'/'Last Seen'. "
            f"Columnas disponibles: {list(df.columns)}"
        )
        return {}

    if online_col:
        online_vals = df[online_col].astype(str).str.strip().str.lower()
        is_online = online_vals.isin({"online", "yes", "true", "1"})
    else:
        is_online = pd.Series(False, index=df.index)

    if last_update_col:
        cutoff = datetime.now() - relativedelta(days=30)
        raw = df[last_update_col].astype(str).str.strip()
        last_seen_dt = pd.to_datetime(raw, errors="coerce", dayfirst=True)
        is_recent = last_seen_dt.notna() & (last_seen_dt >= cutoff)
    else:
        is_recent = pd.Series(False, index=df.index)

    is_active = is_online | is_recent
    online = int(is_active.sum())
    offline = int(len(df) - online)

    return {"online": online, "offline": offline, "total": len(df)}