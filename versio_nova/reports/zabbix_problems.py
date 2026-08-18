from datetime import datetime

from config import COMPANY_TO_ZABBIX_GROUP, ZABBIX_SEVERITY_MAP
from api.zabbix import api_call


def _get_group_ids_for_company(zabbix_group_name: str) -> list:
    """
    Devuelve los groupids del grupo de la empresa Y de todos sus subgrupos
    (ej. 'MEAT CENTER' y 'MEAT CENTER/MAQUINAS VIRTUALES'), ya que en
    Zabbix la jerarquía de grupos se expresa con '/' en el propio nombre.
    """
    r = api_call("hostgroup.get", {"output": ["groupid", "name"]})
    all_groups = r.get("result", [])

    matches = [
        g for g in all_groups
        if g["name"] == zabbix_group_name
        or g["name"].startswith(f"{zabbix_group_name}/")
    ]

    return [g["groupid"] for g in matches]


def fetch_suppressed_acknowledged_problems(company_name: str) -> list:
    """
    Devuelve la lista de problemas de Zabbix para 'company_name' que estén
    SUPRIMIDOS + RECONOCIDOS (ya tratados: ticket creado / en resolución).

    Si la empresa no está en COMPANY_TO_ZABBIX_GROUP (no tiene Zabbix),
    devuelve [] directamente sin llamar a la API.
    """
    zabbix_group_name = COMPANY_TO_ZABBIX_GROUP.get(company_name)
    if not zabbix_group_name:
        return []

    group_ids = _get_group_ids_for_company(zabbix_group_name)
    if not group_ids:
        print(f"      [!] No se encontró el grupo Zabbix '{zabbix_group_name}' para '{company_name}'.")
        return []

    r = api_call(
        "problem.get",
        {
            "groupids": group_ids,
            "acknowledged": True,
            "suppressed": True,
            "output": "extend",
            "selectTags": "extend",
            "sortfield": "eventid",
            "sortorder": "DESC",
        },
    )

    raw_problems = r.get("result", [])
    if not raw_problems:
        return []

    # problem.get no devuelve el host directamente: solo el 'objectid' del
    # trigger que generó el problema. Hay que resolver host por trigger
    # aparte con trigger.get (object == "0" significa que el problema
    # viene de un trigger, que es el caso normal).
    trigger_ids = list({
        p["objectid"] for p in raw_problems if p.get("object") == "0"
    })

    host_by_trigger = {}
    if trigger_ids:
        r_triggers = api_call(
            "trigger.get",
            {
                "triggerids": trigger_ids,
                "output": ["triggerid"],
                "selectHosts": ["name"],
            },
        )
        for t in r_triggers.get("result", []):
            hosts = t.get("hosts", [])
            host_by_trigger[t["triggerid"]] = hosts[0]["name"] if hosts else "N/D"

    problems = []
    for p in raw_problems:
        host_name = host_by_trigger.get(p.get("objectid"), "N/D")
        severity = ZABBIX_SEVERITY_MAP.get(p.get("severity"), "Desconocida")
        clock = datetime.fromtimestamp(int(p["clock"])) if p.get("clock") else None

        problems.append({
            "host": host_name,
            "name": p.get("name"),
            "severity": severity,
            "date": clock,
        })

    return problems