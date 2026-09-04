"""
Script de prueba: comprueba que la conexión a Zabbix funciona y que
trae correctamente los problemas suprimidos+reconocidos de una empresa.

Uso:
    python test_zabbix.py "MEAT CENTER"                       -> todo el histórico
    python test_zabbix.py "MEAT CENTER" 2026-08-01 2026-08-31 -> un periodo concreto
"""

import sys
from datetime import date

from reports.zabbix_problems import fetch_suppressed_acknowledged_problems

if __name__ == "__main__":
    company = sys.argv[1] if len(sys.argv) > 1 else "MEAT CENTER"

    time_from = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else None
    time_till = date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else None

    rango = f" ({time_from} a {time_till})" if time_from else " (SIN filtro de fechas, todo el histórico)"
    print(f"Consultando problemas suprimidos+reconocidos para: {company}{rango}\n")

    problems = fetch_suppressed_acknowledged_problems(company, time_from=time_from, time_till=time_till)

    if not problems:
        print("No se han encontrado problemas (o la empresa no tiene grupo Zabbix asignado).")
    else:
        print(f"Se han encontrado {len(problems)} problemas:\n")
        for p in problems:
            fecha = p["date"].strftime("%d/%m/%Y %H:%M") if p["date"] else "N/D"
            estado = "RESUELTO" if p.get("resolved") else "ACTIVO"
            print(f"  - [{p['severity']}] {p['host']} | {p['name']} | x{p['occurrences']} | {estado} | {fecha}")