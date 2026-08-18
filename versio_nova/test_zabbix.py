"""
Script de prueba: comprueba que la conexión a Zabbix funciona y que
trae correctamente los problemas suprimidos+reconocidos de una empresa.

Uso:
    python test_zabbix.py "MEAT CENTER"
"""

import sys

from reports.zabbix_problems import fetch_suppressed_acknowledged_problems

if __name__ == "__main__":
    company = sys.argv[1] if len(sys.argv) > 1 else "MEAT CENTER"

    print(f"Consultando problemas suprimidos+reconocidos para: {company}\n")

    problems = fetch_suppressed_acknowledged_problems(company)

    if not problems:
        print("No se han encontrado problemas (o la empresa no tiene grupo Zabbix asignado).")
    else:
        print(f"Se han encontrado {len(problems)} problemas:\n")
        for p in problems:
            fecha = p["date"].strftime("%d/%m/%Y %H:%M") if p["date"] else "N/D"
            print(f"  - [{p['severity']}] {p['host']} | {p['name']} | {fecha}")