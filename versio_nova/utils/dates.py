from datetime import datetime
from dateutil.relativedelta import relativedelta

from config import BD_REPORT_INTERVAL


def get_report_interval():
    today = datetime.now()

    if BD_REPORT_INTERVAL == 1:
        label = "Últimas 24 horas"
        start = today - relativedelta(hours=24)
        end = today

    elif BD_REPORT_INTERVAL == 3:
        label = "Últimos 30 días"
        start = today - relativedelta(days=30)
        end = today

    elif BD_REPORT_INTERVAL == 7:
        label = (today - relativedelta(months=1)).strftime("%B %Y").capitalize()

        start = (
            today
            - relativedelta(months=1)
        ).replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        end = today.replace(
            day=1,
            hour=23,
            minute=59,
            second=59,
            microsecond=999,
        ) - relativedelta(days=1)

    else:
        label = today.strftime("%B %Y").capitalize()

        start = today.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        end = today

    start_iso = f"{start.strftime('%Y-%m-%dT%H:%M:%S')}.000Z"
    end_iso = f"{end.strftime('%Y-%m-%dT%H:%M:%S')}.000Z"

    return start_iso, end_iso, label