from datetime import date


def set_date(year, month):
    if month < 1:
        year -= 1
        month = 12
    elif month > 12:
        year += 1
        month = 1
    return {'year':year, 'month':month}


def brl(value):

    if value is None:
        return "R$0.00"

    return f"R${value:,.2f}"


def day_name_number(d):
    return date.strftime(date.fromisoformat(d), "%a %d")


def month_name(m):
    zero = ""
    if m < 10:
        zero = "0"
    return date.strftime(date.fromisoformat(f"2000-{zero}{m}-01"), "%B")