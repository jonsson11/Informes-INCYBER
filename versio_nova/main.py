import argparse
import time

from config import (BD_REPORT_INTERVAL, EXCLUDED_COMPANIES, COMPANY_TO_ZABBIX_GROUP,)
from api.bitdefender import api_call
from api.reports_batch import create_reports, wait_and_download_reports
from reports.security_audit import (build_security_audit_report_params, parse_security_audit_zip,)
from reports.endpoint_status import (build_endpoint_status_report_params, parse_endpoint_status_zip,)
from reports.malware_status import (build_malware_status_report_params, parse_malware_status_zip,)
from reports.quarantine import (fetch_quarantine_items,)
from reports.zabbix_problems import fetch_suppressed_acknowledged_problems
from services.statistics import (compute_stats,)
from pdf.generator import (generate_pdf,)
from services.period import get_period_from_interval


def get_all_endpoints(parent_id, seen=None):
    """
    Devuelve TODOS los endpoints bajo parent_id, incluyendo los que están
    dentro de subcarpetas/grupos personalizados (de forma recursiva),
    paginando si hay más de 100 endpoints en un mismo grupo, y
    deduplicando por ID por si un mismo endpoint aparece a través de
    más de un camino en el árbol de grupos.
    """
    is_root_call = seen is None
    if seen is None:
        seen = {}

    # 1) Endpoints directamente en este grupo (con paginación)
    page = 1
    while True:
        r_eps = api_call("network.getEndpointsList", {
                "parentId": parent_id,
                "perPage": 100,
                "page": page,
            },
        )
        result = r_eps.get("result", {})
        items = result.get("items", [])
        for item in items:
            eid = item.get("id")
            if eid and eid not in seen:
                seen[eid] = item

        pages_count = result.get("pagesCount", 1)
        if page >= pages_count or not items:
            break
        page += 1

    # 2) Subgrupos (custom groups) bajo este parent_id -> recursión
    r_groups = api_call("network.getCustomGroupsList", {"parentId": parent_id})
    subgroups = r_groups.get("result", [])
    for g in subgroups:
        gid = g.get("id")
        if gid:
            get_all_endpoints(gid, seen)

    if is_root_call:
        return list(seen.values())
    return None


def process_company(cid, cname):
    endpoints_raw = get_all_endpoints(cid)
    equipos_reales = [e for e in endpoints_raw if e.get("machineType") in (1, 2)]
    managed_total = len(equipos_reales)

    # --------------------------------------------------
    # Pedimos los 3 informes de BitDefender A LA VEZ y esperamos a los
    # 3 de forma entrelazada (una sola espera compartida), en vez de
    # crear+esperar+descargar cada uno por separado, uno detras de otro.
    # --------------------------------------------------
    report_specs = {
        "endpoint_status": build_endpoint_status_report_params(cid),
        "security_audit": build_security_audit_report_params(cid),
        "malware_status": build_malware_status_report_params(cid),
    }
    report_ids = create_reports(report_specs)
    zips = wait_and_download_reports(report_ids)

    status_summary = parse_endpoint_status_zip(zips.get("endpoint_status"))
    active_total = status_summary.get("online", 0)

    events, _csv_start_ignored, _csv_end_ignored = parse_security_audit_zip(zips.get("security_audit"))

    csv_start, csv_end = get_period_from_interval(BD_REPORT_INTERVAL)
    period_label = f"{csv_start.strftime('%d/%m/%Y')} - {csv_end.strftime('%d/%m/%Y')}"

    malware_actions = parse_malware_status_zip(zips.get("malware_status"))
    quarantine_items = fetch_quarantine_items(cid, start_date=csv_start, end_date=csv_end)

    stats = compute_stats(equipos_reales, managed_total, active_total, events, malware_actions, quarantine_items,)

    has_zabbix = cname in COMPANY_TO_ZABBIX_GROUP
    zabbix_problems = (
        fetch_suppressed_acknowledged_problems(cname, time_from=csv_start, time_till=csv_end)
        if has_zabbix else []
    )

    out = generate_pdf(cname, stats, period_label, period_start=csv_start, has_zabbix=has_zabbix, zabbix_problems=zabbix_problems,)
    return out


def main():

    parser = argparse.ArgumentParser(description="Generador de Informes BitDefender")
    parser.add_argument("-E", "--empresa", type=str, default=None,
                         help="Nombre exacto de la empresa a procesar. Si no se indica, se procesan todas.")
    args = parser.parse_args()

    print("=" * 60)
    print("    INCYBER - Generador de Informes BitDefender")
    print("=" * 60)

    r = api_call("network.getCompaniesList")

    if "error" in r:
        raise RuntimeError(f"Error al obtener empresas: "f"{r['error']}")

    companies = r.get("result", [])
    companies = [c for c in companies if c.get("name") not in EXCLUDED_COMPANIES]

    if args.empresa:
        companies = [c for c in companies if c.get("name") == args.empresa]
        if not companies:
            raise RuntimeError(f"Empresa '{args.empresa}' no encontrada (o está excluida).")

    if not companies:
        raise RuntimeError("No se ha encontrado ninguna empresa en la cuenta de BitDefender.")

    print(f"  [i] Se han encontrado {len(companies)} empresas.\n")

    ok, fail = 0, 0
    for c in companies:
        cid = c.get("id")
        cname = c.get("name")
        print(f"  -> Procesando: {cname}")
        try:
            out = process_company(cid, cname)
            print(f"     [+] PDF generado con éxito: {out}\n")
            ok += 1
        except Exception as e:
            print(f"     [!] Error generando el informe de '{cname}': {e}\n")
            fail += 1

        # Pequeño respiro entre empresas para no saturar la API de BitDefender
        # cuando se procesan varias seguidas (evita rate-limits en la descarga).
        time.sleep(2)

    print("=" * 60)
    print(f"  Completado: {ok} informes generados, {fail} con error.")
    print("=" * 60)


if __name__ == "__main__":
    main()