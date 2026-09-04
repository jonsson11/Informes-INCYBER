import pandas as pd
from datetime import datetime
from pdf.generator import generate_pdf

base_stats = {
    "total_managed": 10, "total_online": 8, "blocked_total": 0,
    "ws_count": 5, "sv_count": 2, "macos_count": 1, "linux_count": 1,
    "phys_count": 3, "virt_count": 6,
    "top5_threats": {}, "action_pcts": {"blocked": 0, "deleted": 0, "quarantine": 0, "disinfected": 0},
    "breakdown_ws": 0, "breakdown_sv": 0,
    "top10_table": pd.DataFrame(columns=["Endpoint", "Detecciones"]),
    "quarantine_table": pd.DataFrame(columns=["Endpoint", "Malware", "Ruta", "Fecha"]),
}

# Caso 1: sin zabbix, tablas vacias, nombre de empresa largo
out1 = generate_pdf(
    "ACTIUM INDUSTRIAL SOLUTIONS INTERNATIONAL S.L.",
    base_stats, "01/08/2026 - 31/08/2026",
    period_start=datetime(2026, 8, 1), has_zabbix=False, zabbix_problems=[],
)
print("Caso 1 OK ->", out1)

# Caso 2: muchas filas para forzar salto de pagina en top10/quarantine/zabbix
many_top10 = pd.DataFrame(
    [(f"WS-EQUIPO-{i:02d}", 30 - i) for i in range(10)],
    columns=["Endpoint", "Detecciones"],
)
many_quarantine = pd.DataFrame(
    [(f"WS-{i:02d}", f"Malware.Sample.{i}", f"C:/Temp/muy/largo/path/de/archivo/sospechoso_{i}_version_final.exe", "01/08/2026") for i in range(20)],
    columns=["Endpoint", "Malware", "Ruta", "Fecha"],
)
stats2 = dict(base_stats)
stats2["top10_table"] = many_top10
stats2["quarantine_table"] = many_quarantine
stats2["top5_threats"] = {"Malware": 10, "Phishing": 5}

many_zabbix = [
    {"host": f"HOST-{i:02d}", "name": f"Problema de prueba numero {i} con texto bastante largo para forzar el wrap", "occurrences": i + 1, "severity": "Media", "resolved": i % 2 == 0, "date": datetime(2026, 8, 1)}
    for i in range(15)
]

out2 = generate_pdf(
    "CELEVANT", stats2, "01/08/2026 - 31/08/2026",
    period_start=datetime(2026, 8, 1), has_zabbix=True, zabbix_problems=many_zabbix,
)
print("Caso 2 OK ->", out2)
