from flask import (
    Blueprint, g, redirect, render_template, url_for
)
from datetime import date

from .auth import login_required
from .accounts import get_account
from .db import get_db
from .utils import set_date

bp = Blueprint('dashboard', __name__)


@bp.before_app_request
def set_current_date():
    g.date = {
        'month':date.strftime(date.today(), "%m"), 
        'year':int(date.strftime(date.today(), "%Y"))
        }


def get_transaction_total(type, year, month):
    zero = ""
    if month < 10: 
        zero = "0"
    return get_db().execute(
        "SELECT SUM(t.amount) "
        "FROM transactions t "
        "JOIN account a "
        "ON t.account_id_origin = a.id "
        "JOIN transaction_type tt "
        "ON t.type_id = tt.id "
        "WHERE tt.type = ? "
        "AND strftime('%Y', t.date) = ? "
        "AND strftime('%m', t.date) = ? "
        "AND a.user_id = ?", (type, str(year), f"{zero}{month}", g.user['id'])
    ).fetchone()[0]


@bp.route('/')
@login_required
def index():
    return redirect(url_for('.main', year=g.date['year'], month=g.date['month']))


@bp.route('/<int:year>/<int:month>')
@login_required
def main(year, month):
    if month < 1 or month > 12:
        return redirect(url_for('.main', year=set_date(year, month)["year"], month=set_date(year, month)['month']))
    
    accounts = get_account(get_all=True)
    
    balance = 0.0
    for account in accounts:
        balance += account['amount']

    income_total = get_transaction_total("incomes", year, month)
    expense_total = get_transaction_total("expenses", year, month)

    last_expenses = get_db().execute(
            "SELECT t.id, t.description, t.amount, strftime('%Y/%m/%d', t.date) AS date, a.name AS account "
            "FROM transactions t "
            "JOIN transaction_type tt "
            "ON t.type_id = tt.id "
            "JOIN account a "
            "ON t.account_id_origin = a.id "
            "WHERE tt.type = ? "
            "AND a.user_id = ? "
            "ORDER BY t.date DESC "
            "LIMIT 5", ('expenses', g.user['id'])
        ).fetchall()

    return render_template('dashboard/main.html', accounts=accounts, balance=balance, income_total=income_total, expense_total=expense_total, last_expenses=last_expenses, year=year, month=month)