import io
import time

import pandas as pd

from config import BD_REPORT_INTERVAL, MODULE_TO_CATEGORY, REPORT_TYPE_SECURITY_AUDIT
from api.reports_batch import extract_csv_from_zip


def build_security_audit_report_params(cid: str) -> dict:
    """Parametros para crear el informe Security Audit (sin crearlo ni esperar)."""
    return {
        "type": REPORT_TYPE_SECURITY_AUDIT,
        "name": f"INCYBER_SecurityAudit_{int(time.time())}",
        "targetIds": [cid],
        "options": {"reportingInterval": BD_REPORT_INTERVAL},
    }


def parse_security_audit_zip(z_bytes: bytes):
    """
    A partir del ZIP ya descargado del informe Security Audit, devuelve
    una lista de eventos con endpointName/category/occurrences, y el
    rango real de fechas (csv_start, csv_end) segun el propio CSV.
    """
    content = extract_csv_from_zip(z_bytes)
    if not content:
        return [], None, None

    sep = ";" if ";" in content.splitlines()[0] else ","
    df = pd.read_csv(io.StringIO(content), sep=sep, on_bad_lines="skip")
    df.columns = [c.strip() for c in df.columns]

    csv_start = None
    csv_end = None

    date_col = next(
        (c for c in df.columns if c.strip().lower() == "last occurrence"),
        None,
    )

    if date_col:
        dates = pd.to_datetime(df[date_col], format="%d %B %Y, %H:%M:%S", errors="coerce")
        dates = dates.dropna()
        if not dates.empty:
            csv_start = dates.min()
            csv_end = dates.max()

    endpoint_col = next((c for c in df.columns if "endpoint" in c.lower() and "fqdn" not in c.lower()), None)
    module_col = next((c for c in df.columns if c.lower() == "module"), None)
    occ_col = next((c for c in df.columns if "occurrence" in c.lower()), None)
    event_type_col = next((c for c in df.columns if c.strip().lower() == "event type"), None)

    if not endpoint_col:
        return [], None, None

    events = []

    for _, row in df.iterrows():
        ep_val = str(row[endpoint_col]).strip()
        if not ep_val or ep_val.lower() == "nan":
            continue
        try:
            occ_val = max(1, int(float(row[occ_col]))) if occ_col else 1
        except (ValueError, TypeError):
            occ_val = 1

        module_val = str(row[module_col]).strip().lower() if module_col else ""
        category = MODULE_TO_CATEGORY.get(module_val, module_val.title() or "Otros")

        event_type_val = str(row[event_type_col]).strip() if event_type_col else ""
        events.append({
            "endpointName": ep_val,
            "category": category,
            "occurrences": occ_val,
            "eventType": event_type_val,
        })

    return events, csv_start, csv_end