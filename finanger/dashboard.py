from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from finanger.auth import login_required
from finanger.accounts import get_account
from finanger.db import get_db

bp = Blueprint('dashboard', __name__)


def brl(value):

    if value is None:
        return "R$0.00"

    return f"R${value:,.2f}"


@bp.route('/')
@login_required
def index():

    accounts = get_account(get_all=True)
    balance = 0.0
    for account in accounts:
        balance += account['amount']

    db = get_db()

    income_total = db.execute(
        'SELECT SUM(t.amount) FROM transactions t '
        'JOIN account a ON t.account_id = a.id '
        'WHERE t.type_id = 1 AND a.user_id = ?', (g.user['id'],)
    ).fetchone()[0]
    
    expense_total = db.execute(
        'SELECT SUM(t.amount) FROM transactions t '
        'JOIN account a ON t.account_id = a.id '
        'WHERE t.type_id = 2 AND a.user_id = ?', (g.user['id'],)
    ).fetchone()[0]

    last_expenses = db.execute(
            "SELECT t.id, t.description, t.amount, t.date, a.name AS account "
            "FROM transactions t "
            "JOIN transaction_type tt ON t.type_id = tt.id "
            "JOIN account a ON t.account_id = a.id "
            "WHERE tt.type = ? AND a.user_id = ? "
            "ORDER BY t.date DESC "
            "LIMIT 5", ('expenses', g.user['id'])
        ).fetchall()

    return render_template('dashboard/index.html', accounts=accounts, balance=balance, income_total=income_total, expense_total=expense_total, last_expenses=last_expenses)