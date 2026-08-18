from collections import Counter

import pandas as pd


def compute_stats(
    equipos_reales: list,
    managed_total: int,
    active_total: int,
    events: list,
    malware_actions: dict = None,
    quarantine_items: list = None,
) -> dict:

    # --------------------------------------------------
    # Físicos vs Virtuales -> viene de machineType
    # (1 = computer/físico, 2 = virtual machine, 3 = EC2, 0 = Other)
    # --------------------------------------------------

    phys_count = sum(1 for e in equipos_reales if e.get("machineType") == 1)
    virt_count = sum(1 for e in equipos_reales if e.get("machineType") == 2)

    # --------------------------------------------------
    # Windows WS vs Windows SRV -> viene de operatingSystemVersion
    # (machineType NO indica esto, indica físico/virtual)
    # --------------------------------------------------

    def is_windows_server(e):
        os_str = str(e.get("operatingSystemVersion", "")).lower()
        return "windows" in os_str and "server" in os_str

    def is_mac(e):
        return "mac" in str(e.get("operatingSystemVersion", "")).lower()

    def is_linux(e):
        os_str = str(e.get("operatingSystemVersion", "")).lower()
        linux_keywords = ["linux", "rocky", "rhel", "red hat", "ubuntu", "debian", "suse", "centos", "fedora", "alpine"]
        return any(keyword in os_str for keyword in linux_keywords)

    sv_count = 0
    mac_count = 0
    linux_count = 0
    ws_count = 0

    for e in equipos_reales:
        os_str = str(e.get("operatingSystemVersion", ""))

        if is_windows_server(e):
            sv_count += 1
        elif is_mac(e):
            mac_count += 1
        elif is_linux(e):
            linux_count += 1
        else:
            # AHORA SÍ: Si no es Server, ni Mac, ni Linux, entra aquí por cada equipo (Windows normal)
            ws_count += 1

    blocked_total = sum(e["occurrences"]for e in events)
    threat_counts = Counter()

    for e in events:
        threat_counts[e["category"]] += e["occurrences"]

    top5_threats = dict(
        sorted(
            threat_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]
    )

    # --------------------------------------------------
    # Desglose amenazas por tipo de endpoint (Workstations/Servidores)
    # -> también debe basarse en operatingSystemVersion, no en machineType
    # --------------------------------------------------

    server_by_name = {
        e.get("name", "").upper(): is_windows_server(e)
        for e in equipos_reales
    }

    breakdown_ws = 0
    breakdown_sv = 0

    for e in events:
        is_server = server_by_name.get(
            e["endpointName"].upper(),
            False,
        )

        if is_server:
            breakdown_sv += e["occurrences"]
        else:
            breakdown_ws += e["occurrences"]

    # Top 10 endpoints
    detections_by_endpoint = Counter()

    for e in events:
        detections_by_endpoint[
            e["endpointName"]
        ] += e["occurrences"]

    top10_table = pd.DataFrame(
        sorted(
            detections_by_endpoint.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10],
        columns=[
            "Endpoint",
            "Detecciones",
        ],
    )

    quarantine_table = pd.DataFrame(
        quarantine_items or [],
        columns=["Endpoint", "Malware", "Ruta", "Fecha"],
    )


    # --------------------------------------------------
    # Acciones de remediacion. Las categorias Phishing, Initial Access,
    # Discovery, Web Traffic Scan (y los submodulos advanced anti-exploit
    # y blocklist dentro de "Malware") no trabajan con archivos: bloquean
    # una web, un puerto, un exploit o un hash, sin mas accion posible.
    # Por tanto van integramente a "Bloqueado".
    #
    # El desglose real (Cleaned/Ignored/Quarantined/Deleted/Unresolved)
    # solo existe para detecciones de archivo del modulo Antimalware, y
    # viene del informe Malware Status (type 12), no de Security Audit.
    # --------------------------------------------------

    malware_actions = malware_actions or {}
    quarantine_items = quarantine_items or []

    ms_cleaned = malware_actions.get("Cleaned", 0)
    ms_ignored = malware_actions.get("Ignored", 0)
    ms_quarantined = malware_actions.get("Quarantined", 0)
    ms_deleted = malware_actions.get("Deleted", 0)
    ms_unresolved = malware_actions.get("Unresolved", 0)

    malware_status_total = (
        ms_cleaned + ms_ignored + ms_quarantined + ms_deleted + ms_unresolved
    )

    # La categoria "Cuarentena" del desglose usa el recuento REAL del
    # almacen de cuarentena (getQuarantineItemsList), no el snapshot de
    # acciones de Malware Status: un archivo puede acabar en cuarentena
    # (intervencion manual, segunda pasada de escaneo, etc.) sin que el
    # informe Malware Status lo clasifique como "Quarantined" en su
    # snapshot. Asi la tabla "Elementos en Cuarentena" y el porcentaje
    # de Cuarentena siempre cuadran entre si.
    real_quarantined = len(quarantine_items)

    # Todo lo que no esta cubierto por el desglose de Malware Status
    # (Phishing, Initial Access, Discovery, Web Traffic Scan, anti-exploit,
    # blocklist, y cualquier evento de Malware no capturado por el type 12)
    # se considera "Bloqueado".
    #
    # "Ignored" y "Unresolved" tambien se consideran "Bloqueado": no hay
    # una accion de remediacion real sobre el archivo, asi que se suman
    # al mismo cubo en vez de tener categoria propia.
    #
    # Restamos ms_quarantined (ya incluido implicitamente en
    # malware_status_total) y sumamos real_quarantined para que el total
    # de Bloqueado no descuadre al cambiar la fuente de Cuarentena.
    blocked_count = max(
        0, blocked_total - malware_status_total
    ) + ms_unresolved + ms_ignored + ms_quarantined - real_quarantined
    blocked_count = max(0, blocked_count)

    # El denominador tiene que ser autoconsistente: la suma de los propios
    # cuatro cubos que se reparten el 100%, no "blocked_total" (que viene
    # de una fuente ajena, Security Audit, y no guarda relacion 1:1 con
    # el numero de filas individuales de la cuarentena). Si se usa
    # blocked_total como denominador, un endpoint con pocas amenazas
    # "oficiales" pero muchos archivos en cuarentena puede dar porcentajes
    # por encima del 100% (ej. 14 archivos / 3 amenazas = 466.7%).
    remediation_total = (
        blocked_count + ms_deleted + real_quarantined + ms_cleaned
    )

    if remediation_total > 0:
        action_pcts = {
            "blocked": round((blocked_count / remediation_total) * 100, 1),
            "deleted": round((ms_deleted / remediation_total) * 100, 1),
            "quarantine": round((real_quarantined / remediation_total) * 100, 1),
            "disinfected": round((ms_cleaned / remediation_total) * 100, 1),
        }
    else:
        action_pcts = {
            "blocked": 0.0,
            "deleted": 0.0,
            "quarantine": 0.0,
            "disinfected": 0.0,
        }

    # Cinturon de seguridad: aunque remediation_total ya hace que los
    # porcentajes sumen 100% de forma consistente, se limita cada valor
    # a 100.0 por si en el futuro alguna fuente (Malware Status vs
    # Quarantine store) queda desincronizada por un desfase de periodo.
    action_pcts = {k: min(v, 100.0) for k, v in action_pcts.items()}

    return {
        "total_managed": managed_total,
        "total_online": active_total,
        "blocked_total": blocked_total,
        "ws_count": ws_count,
        "sv_count": sv_count,
        "macos_count": mac_count,
        "linux_count": linux_count,
        "phys_count": phys_count,
        "virt_count": virt_count,
        "top5_threats": top5_threats,
        "action_pcts": action_pcts,
        "breakdown_ws": breakdown_ws,
        "breakdown_sv": breakdown_sv,
        "top10_table": top10_table,
        "quarantine_table": quarantine_table,
    }