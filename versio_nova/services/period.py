from datetime import date, timedelta
import calendar


def get_period_from_interval(interval_code: int, ref_date: date | None = None) -> tuple[date, date]:
    """
    Devuelve (fecha_inicio, fecha_fin) correspondientes al código de intervalo
    de BitDefender, tomando como referencia 'ref_date' (por defecto: hoy).
    No depende de los datos del CSV, solo del código y la fecha actual.
    """
    today = ref_date or date.today()

    if interval_code == 0:  # TODAY
        start = end = today

    elif interval_code == 1:  # YESTERDAY
        start = end = today - timedelta(days=1)

    elif interval_code == 2:  # THIS WEEK (lunes -> hoy... o lunes -> domingo)
        start = today - timedelta(days=today.weekday())  # lunes de esta semana
        end = start + timedelta(days=6)                  # domingo de esta semana

    elif interval_code == 3:  # LAST WEEK
        this_monday = today - timedelta(days=today.weekday())
        start = this_monday - timedelta(days=7)
        end = this_monday - timedelta(days=1)

    elif interval_code == 4:  # THIS MONTH
        start = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end = today.replace(day=last_day)

    elif interval_code == 5:  # LAST MONTH
        first_this_month = today.replace(day=1)
        end = first_this_month - timedelta(days=1)
        start = end.replace(day=1)

    elif interval_code == 6:  # LAST 2 MONTHS
        first_this_month = today.replace(day=1)
        end = first_this_month - timedelta(days=1)
        start_month_first = end.replace(day=1)
        # retrocedemos un mes más para coger el inicio
        prev_month_last_day = start_month_first - timedelta(days=1)
        start = prev_month_last_day.replace(day=1)

    elif interval_code == 7:  # LAST 3 MONTHS
        first_this_month = today.replace(day=1)
        end = first_this_month - timedelta(days=1)
        m = end.month - 2
        y = end.year
        while m <= 0:
            m += 12
            y -= 1
        start = date(y, m, 1)

    elif interval_code == 8:  # THIS YEAR
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)

    elif interval_code == 9:  # LAST YEAR
        start = date(today.year - 1, 1, 1)
        end = date(today.year - 1, 12, 31)

    else:
        raise ValueError(f"BD_REPORT_INTERVAL desconocido: {interval_code}")

    return start, end