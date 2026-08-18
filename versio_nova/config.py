import os
import sys

# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------
# 0 - TODAY
# 1 - YESTERDAY
# 2 - THIS WEEK
# 3 - LAST WEEK
# 4 - THIS MONTH
# 5 - LAST MONTH
# 6 - LAST 2 MONTHS
# 7 - LAST 3 MONTHS
# 8 - THIS YEAR
# 9 - LAST YEAR
# --------------------------------------------------

BD_REPORT_INTERVAL = 4

BASE_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))
ASSETS_PATH = os.path.join(BASE_PATH, "assets")
OUTPUT_DIR = os.path.join(BASE_PATH, "informes")

# Empresas a excluir del listado (la propia MSP, etc.)
EXCLUDED_COMPANIES = ["INCYBER"]


logo_portada = os.path.join(ASSETS_PATH, "logo_portada.png")
logo_encabezado = os.path.join(ASSETS_PATH, "logo_encabezado.png")
icon_portada = os.path.join(ASSETS_PATH, "icon_portada.png")

# Iconos para la tabla de Inventario (assets/icons/)
ICONS_PATH = os.path.join(ASSETS_PATH, "icons")
icon_windows = os.path.join(ICONS_PATH, "windows.png")
icon_linux = os.path.join(ICONS_PATH, "linux.png")
icon_macos = os.path.join(ICONS_PATH, "apple.png")
icon_server = os.path.join(ICONS_PATH, "server.png")
icon_managed = os.path.join(ICONS_PATH, "display.png")
icon_active = os.path.join(ICONS_PATH, "wifi.png")
icon_shield = os.path.join(ICONS_PATH, "shield.png")
icon_physical = os.path.join(ICONS_PATH, "physical.png")
icon_virtual = os.path.join(ICONS_PATH, "virtual.png")

# --------------------------------------------------
# API BITDEFENDER
# --------------------------------------------------

API_KEY = "720fe45e020368bc278b2ea80be98c7f445f5bf4ce9ae8ae8294f29b68716b62"
API_HOST = "https://cloudgz.gravityzone.bitdefender.com/api/v1.0/jsonrpc"

REPORT_TYPE_SECURITY_AUDIT = 17
REPORT_TYPE_ENDPOINT_PROTECTION_STATUS = 8

MODULE_TO_CATEGORY = {
    "antiphishing": "Phishing",
    "network attack defense": "Initial Access",
    "firewall": "Discovery",
    "antimalware": "Malware",
    "content control": "Phishing",
    "advanced anti-exploit": "Malware",
    "blocklist": "Malware",
}

# --------------------------------------------------
# API ZABBIX
# --------------------------------------------------
# Zabbix 7.4 -> autenticación por API Token fijo (header Authorization: Bearer)
# Se crea desde: Administración > Usuarios > (tu usuario) > Tokens API

ZABBIX_API_HOST = "https://watch.incyber.es/api_jsonrpc.php"  # <-- ajustar URL real
ZABBIX_API_TOKEN = "e9735c83c24fc256232d6aca7919de90ebb7d2f57fa818123f959797755bd8e0"  # <-- ajustar token real

# Mapeo empresa (nombre en BitDefender) -> nombre del Host Group en Zabbix.
# Solo las empresas que aparecen aquí tendrán sección de Zabbix en el PDF.
# Las que coincidan de nombre exacto se mapean 1:1; las que no, con su
# nombre real en Zabbix (ej. GSP PORCSA -> "GSP").
COMPANY_TO_ZABBIX_GROUP = {
    "ACTIUM": "ACTIUM",
    "CELEVANT": "CELEVANT",
    "GSP PORCSA": "GSP",
    "MEAT CENTER": "MEAT CENTER",
    "SIEF2": "SIEF2",
}

# Severidades de Zabbix (problem.get -> campo "severity")
ZABBIX_SEVERITY_MAP = {
    "0": "No clasificado",
    "1": "Información",
    "2": "Advertencia",
    "3": "Media",
    "4": "Alta",
    "5": "Desastre",
}