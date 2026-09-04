from collections import OrderedDict
from datetime import datetime, date, time as dt_time

from config import COMPANY_TO_ZABBIX_GROUP, ZABBIX_SEVERITY_MAP
from api.zabbix import api_call


# Cache en memoria: hostgroup.get devuelve el mismo listado completo para
# todas las empresas, así que se pide UNA sola vez por ejecución del
# programa en lugar de una vez por cada empresa (15 llamadas -> 1).
_ALL_GROUPS_CACHE = None


def _get_all_zabbix_groups() -> list:
    global _ALL_GROUPS_CACHE
    if _ALL_GROUPS_CACHE is None:
        r = api_call("hostgroup.get", {"output": ["groupid", "name"]})
        _ALL_GROUPS_CACHE = r.get("result", [])
    return _ALL_GROUPS_CACHE


def _get_group_ids_for_company(zabbix_group_name: str) -> list:
    """
    Devuelve los groupids del grupo de la empresa Y de todos sus subgrupos
    (ej. 'MEAT CENTER' y 'MEAT CENTER/MAQUINAS VIRTUALES'), ya que en
    Zabbix la jerarquía de grupos se expresa con '/' en el propio nombre.
    """
    all_groups = _get_all_zabbix_groups()

    matches = [
        g for g in all_groups
        if g["name"] == zabbix_group_name
        or g["name"].startswith(f"{zabbix_group_name}/")
    ]

    return [g["groupid"] for g in matches]


def fetch_suppressed_acknowledged_problems(
    company_name: str,
    time_from: datetime = None,
    time_till: datetime = None,
) -> list:
    """
    Devuelve la lista de problemas de Zabbix para 'company_name' que estén
    RECONOCIDOS y que en algún momento se hayan SUPRIMIDO manualmente
    (ya tratados: ticket creado / en resolución), agrupados por
    (host, problema) con un contador de 'occurrences' y la fecha de la
    detección MÁS RECIENTE, ordenados de más reciente a más antiguo.
    Cada grupo incluye también 'resolved' (bool): si la ocurrencia más
    reciente del grupo ya se resolvió en Zabbix o sigue activa.

    Se usa event.get en lugar de problem.get: problem.get solo devuelve
    problemas activos (o resueltos muy recientemente, según el ajuste
    "Display OK triggers for N seconds" de Zabbix), así que en una ventana
    de un mes se perderían los que ya se cerraron. event.get sí mantiene
    el histórico completo filtrado por fecha.

    La condición de "suprimido" se comprueba a partir del historial de
    acciones del evento (selectAcknowledges) en vez del flag "suppressed"
    en vivo, para que un problema tratado no desaparezca de la tabla solo
    porque el mantenimiento/supresión ya haya terminado (ver comentario
    junto a ACTION_SUPPRESS_BIT más abajo).

    Si se pasan time_from/time_till, se filtra por el periodo del informe
    (mismo periodo que BD_REPORT_INTERVAL usa para BitDefender).

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

    def _to_unix(value, end_of_day=False):
        """Acepta tanto date como datetime y devuelve un timestamp unix."""
        if value is None:
            return None
        if isinstance(value, datetime):
            dt_value = value
        else:
            dt_value = datetime.combine(value, dt_time.max if end_of_day else dt_time.min)
        return int(dt_value.timestamp())

    params = {
        "groupids": group_ids,
        "acknowledged": True,
        "value": 1,  # solo eventos de tipo "problema" (no los de "OK"/recuperación)
        "output": "extend",
        "selectTags": "extend",
        # NOTA: no filtramos aquí por "suppressed": True. Ese flag refleja
        # si el evento está suprimido AHORA MISMO (depende de si sigue
        # vigente el mantenimiento/supresión activa), no si estuvo
        # suprimido en su momento. Si el mantenimiento ya terminó, un
        # problema que sí se trató (se suprimió manualmente) dejaría de
        # cumplir ese filtro y desaparecería de la tabla en vez de pasar
        # a RESUELTO. En su lugar pedimos el historial de acciones
        # (selectAcknowledges) y comprobamos abajo si en algún momento se
        # ejecutó la acción "suprimir evento" (bit 32), que sí queda
        # registrada de forma permanente.
        "selectAcknowledges": "extend",
        "sortfield": "eventid",
        "sortorder": "DESC",
    }
    ACTION_SUPPRESS_BIT = 32

    ts_from = _to_unix(time_from, end_of_day=False)
    ts_till = _to_unix(time_till, end_of_day=True)
    if ts_from is not None:
        params["time_from"] = ts_from
    if ts_till is not None:
        params["time_till"] = ts_till

    r = api_call("event.get", params)
    raw_problems = r.get("result", [])
    if not raw_problems:
        return []

    # Nos quedamos solo con los eventos que en algún momento de su
    # historial recibieron la acción manual "suprimir evento" (bit 32).
    # Es el equivalente persistente al filtro "suppressed": True, pero
    # que no se pierde si el mantenimiento/supresión ya terminó.
    def _was_ever_suppressed(problem: dict) -> bool:
        for ack in problem.get("acknowledges") or []:
            try:
                if int(ack.get("action", 0)) & ACTION_SUPPRESS_BIT:
                    return True
            except (TypeError, ValueError):
                continue
        return False

    raw_problems = [p for p in raw_problems if _was_ever_suppressed(p)]
    if not raw_problems:
        return []

    # event.get no devuelve el host directamente: solo el 'objectid' del
    # trigger que generó el evento. Hay que resolver host por trigger
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

    # --------------------------------------------------
    # Agrupar por (host, problema): mismo problema en la misma
    # máquina varias veces -> "occurrences" + fecha/estado de la última.
    # --------------------------------------------------
    grouped = OrderedDict()

    for p in raw_problems:
        host_name = host_by_trigger.get(p.get("objectid"), "N/D")
        name = p.get("name")
        severity = ZABBIX_SEVERITY_MAP.get(p.get("severity"), "Desconocida")
        clock = datetime.fromtimestamp(int(p["clock"])) if p.get("clock") else None
        # r_eventid == "0" -> el evento sigue sin resolver (aún activo).
        # cualquier otro valor -> ya existe un evento de recuperación.
        resolved = p.get("r_eventid", "0") != "0"

        key = (host_name, name)

        if key not in grouped:
            grouped[key] = {
                "host": host_name,
                "name": name,
                "severity": severity,
                "date": clock,
                "occurrences": 1,
                "resolved": resolved,
            }
        else:
            grouped[key]["occurrences"] += 1
            if clock and (grouped[key]["date"] is None or clock > grouped[key]["date"]):
                grouped[key]["date"] = clock
                grouped[key]["severity"] = severity
                grouped[key]["resolved"] = resolved

    problems = sorted(
        grouped.values(),
        key=lambda x: x["date"] or datetime.min,
        reverse=True,
    )

    return problems