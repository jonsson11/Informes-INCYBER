import io
import time
import zipfile

import pandas as pd
import requests

from api.bitdefender import HEADERS, api_call
from config import BD_REPORT_INTERVAL, MODULE_TO_CATEGORY, REPORT_TYPE_SECURITY_AUDIT


def fetch_security_audit_events(cid: str):
    """
    Crea un informe instantáneo Security Audit, espera a que esté listo,
    descarga el CSV y devuelve una lista de eventos con:
      - endpointName
      - category   (Phishing / Initial Access / Discovery / Malware / ...)
      - occurrences
    Cada fila del CSV ya viene agregada por endpoint+detección, con el
    número de repeticiones en la columna "Occurrences".
    """

    
    params_report = {
        "type": REPORT_TYPE_SECURITY_AUDIT,
        "name": f"INCYBER_SecurityAudit_{int(time.time())}",
        "targetIds": [cid],
        "options": {"reportingInterval": BD_REPORT_INTERVAL},
    }

    r_create = api_call("reports.createReport", params_report)
    report_id = r_create.get("result")
    if not report_id:
        print(f"      [!] No se pudo crear el informe: {r_create.get('error')}")
        return [], None, None

    url_csv = None
    for _ in range(10):
        time.sleep(3)
        r_links = api_call("reports.getDownloadLinks", {"reportId": report_id})
        if "error" in r_links:
            print(f"      [!] Error consultando getDownloadLinks: {r_links['error']}")
            time.sleep(3)
            continue
        result = r_links.get("result", {})
        if result.get("readyForDownload"):
            url_csv = result.get("lastInstanceUrl")
            break

    if not url_csv:
        print("      [!] El informe no estuvo listo a tiempo.")
        return [], None, None

    # La descarga puede fallar (rate-limit, fichero aún no propagado, etc.)
    # aunque la API diga readyForDownload=True, así que reintentamos y
    # comprobamos explícitamente que lo recibido es un ZIP válido.
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
        print("      [!] La descarga del informe no es un ZIP válido tras varios intentos.")
        print(f"      [debug] {last_debug}")
        return [], None, None

    with zipfile.ZipFile(io.BytesIO(z_bytes)) as z:
        csv_name = next((n for n in z.namelist() if n.endswith(".csv")), None)
        if not csv_name:
            return [], None, None
        content = z.read(csv_name).decode("utf-8", errors="ignore")

    sep = ";" if ";" in content.splitlines()[0] else ","
    df = pd.read_csv(io.StringIO(content), sep=sep, on_bad_lines="skip")
    df.columns = [c.strip() for c in df.columns]
    # --------------------------------------------------
# RANGO REAL DEL INFORME SEGÚN EL CSV
# --------------------------------------------------

    csv_start = None
    csv_end = None

    date_col = next(
        (
            c
            for c in df.columns
            if c.strip().lower() == "last occurrence"
        ),
        None
    )

    if date_col:

        dates = pd.to_datetime(df[date_col],format="%d %B %Y, %H:%M:%S",errors="coerce")
        dates = dates.dropna()
        if not dates.empty:
            csv_start = dates.min()
            csv_end = dates.max()

    endpoint_col = next((c for c in df.columns if "endpoint" in c.lower() and "fqdn" not in c.lower()),None)
    module_col = next((c for c in df.columns if c.lower() == "module"),None)
    occ_col = next((c for c in df.columns if "occurrence" in c.lower()),None)
    event_type_col = next((c for c in df.columns if c.strip().lower() == "event type"),None)

    if not endpoint_col:
        return [], None, None

    events = []

    for _, row in df.iterrows():

        ep_val = str(row[endpoint_col]).strip()
        if (not ep_val or ep_val.lower() == "nan"):continue
        try:
            occ_val = (max(1,int(float(row[occ_col])))if occ_col else 1)

        except (ValueError,TypeError):
            occ_val = 1

        module_val = (str(row[module_col]).strip().lower() if module_col else "")

        category = MODULE_TO_CATEGORY.get(
            module_val,
            module_val.title() or "Otros"
        )

        event_type_val = (str(row[event_type_col]).strip()if event_type_col else "")
        events.append({
                "endpointName": ep_val,
                "category": category,
                "occurrences": occ_val,
                "eventType": event_type_val,
            }
        )

    return events, csv_start, csv_end