import io
import time
import zipfile

import requests

from api.bitdefender import api_call, HEADERS


def create_reports(report_specs: dict) -> dict:
    """
    Crea varios informes de BitDefender A LA VEZ (una llamada API por cada
    uno, seguidas, sin esperar a que ninguno termine de generarse).

    report_specs: {clave: params_de_reports.createReport}
    Devuelve: {clave: report_id} (solo las que se crearon con éxito)
    """
    report_ids = {}
    for key, params in report_specs.items():
        r = api_call("reports.createReport", params)
        rid = r.get("result")
        if not rid:
            print(f"      [!] No se pudo crear el informe '{key}': {r.get('error')}")
            continue
        report_ids[key] = rid
    return report_ids


def wait_and_download_reports(report_ids: dict, max_polls: int = 10, poll_interval: int = 3) -> dict:
    """
    Espera de forma ENTRELAZADA a que varios informes esten listos, en vez
    de esperar el tiempo completo de cada uno por separado. En cada ronda
    de 'poll_interval' segundos se comprueban TODOS los informes pendientes
    a la vez, asi el tiempo total de espera es aprox. el maximo de los
    informes, no la suma de todos.

    report_ids: {clave: report_id}
    Devuelve: {clave: zip_bytes} (solo los que se descargaron con éxito)
    """
    pending = dict(report_ids)
    urls = {}

    for _ in range(max_polls):
        if not pending:
            break
        time.sleep(poll_interval)
        for key, rid in list(pending.items()):
            r_links = api_call("reports.getDownloadLinks", {"reportId": rid})
            if "error" in r_links:
                continue
            result = r_links.get("result", {})
            if result.get("readyForDownload"):
                urls[key] = result.get("lastInstanceUrl")
                del pending[key]

    for key in pending:
        print(f"      [!] El informe '{key}' no estuvo listo a tiempo.")

    results = {}
    for key, url in urls.items():
        z_bytes = None
        last_debug = ""
        for attempt in range(4):
            r_file = requests.get(url, headers=HEADERS)
            content = r_file.content
            if r_file.status_code == 200 and content[:2] == b"PK":
                z_bytes = content
                break
            last_debug = (
                f"status={r_file.status_code} "
                f"content-type={r_file.headers.get('Content-Type')} "
                f"len={len(content)} body_start={content[:200]!r}"
            )
            time.sleep(3)

        if z_bytes is None:
            print(f"      [!] La descarga del informe '{key}' no es un ZIP válido tras varios intentos.")
            print(f"      [debug] {last_debug}")
            continue

        results[key] = z_bytes

    return results


def extract_csv_from_zip(z_bytes: bytes):
    """Devuelve el contenido de texto del primer CSV dentro de un ZIP, o None."""
    if not z_bytes:
        return None
    with zipfile.ZipFile(io.BytesIO(z_bytes)) as z:
        csv_name = next((n for n in z.namelist() if n.endswith(".csv")), None)
        if not csv_name:
            return None
        return z.read(csv_name).decode("utf-8", errors="ignore")