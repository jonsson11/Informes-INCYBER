"""
Harness de prueba local: genera un PDF con datos sinteticos para
verificar visualmente el nuevo estilo de marca sin llamar a las APIs
reales de BitDefender/Zabbix.
"""
import sys
from datetime import datetime, timedelta

import pandas as pd

from pdf.generator import generate_pdf

stats = {
    "total_managed": 42,
    "total_online": 39,
    "blocked_total": 128,
    "ws_count": 24,
    "sv_count": 8,
    "macos_count": 4,
    "linux_count": 6,
    "phys_count": 14,
    "virt_count": 28,
    "top5_threats": {
        "Malware": 48,
        "Phishing": 22,
        "Initial Access": 15,
        "Discovery": 9,
        "Ransomware": 5,
    },
    "action_pcts": {
        "blocked": 52.3,
        "deleted": 18.1,
        "quarantine": 21.4,
        "disinfected": 8.2,
    },
    "breakdown_ws": 70,
    "breakdown_sv": 29,
    "top10_table": pd.DataFrame(
        [
            ("SRV-FILE-02", 18),
            ("WS-COMERCIAL-07", 14),
            ("SRV-DC-01", 9),
            ("WS-ADMIN-03", 7),
            ("WS-CONTABILIDAD-11", 6),
            ("SRV-BACKUP-01", 5),
            ("WS-RRHH-02", 4),
            ("WS-LOGISTICA-05", 3),
            ("SRV-WEB-01", 2),
            ("WS-DIRECCION-01", 1),
        ],
        columns=["Endpoint", "Detecciones"],
    ),
    "quarantine_table": pd.DataFrame(
        [
            ("SRV-FILE-02", "Trojan.GenericKD.71834112", "C:/Users/Public/Downloads/invoice_2026.exe", "28/08/2026"),
            ("WS-COMERCIAL-07", "Ransom.Phobos.Gen", "C:/ProgramData/Temp/update_svc.dll", "27/08/2026"),
            ("WS-ADMIN-03", "HackTool.PowerSploit.A", "C:/Windows/Temp/ps_inject_payload_stage2_final_version.ps1", "22/08/2026"),
        ],
        columns=["Endpoint", "Malware", "Ruta", "Fecha"],
    ),
}

zabbix_problems = [
    {"host": "GSP-SW-CORE-01", "name": "High CPU utilization on core switch", "occurrences": 5, "severity": "Alta", "resolved": False, "date": datetime(2026, 8, 28, 9, 14)},
    {"host": "GSP-NAS-01", "name": "Disk space is low on volume /data", "occurrences": 2, "severity": "Media", "resolved": True, "date": datetime(2026, 8, 30, 22, 41)},
]

period_start = datetime(2026, 8, 1)
period_label = "01/08/2026 - 31/08/2026"

out = generate_pdf(
    "GSP PORCSA",
    stats,
    period_label,
    period_start=period_start,
    has_zabbix=True,
    zabbix_problems=zabbix_problems,
)
print("OK ->", out)
