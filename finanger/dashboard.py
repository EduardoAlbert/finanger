from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from finanger.auth import login_required
from finanger.accounts import get_account
from finanger.db import get_db

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():

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
    
    accounts = get_account()
    balance = 0.0
    for account in accounts:
        balance += account['amount']
    balance = f"{balance:.2f}"
    return render_template('dashboard/index.html', accounts=accounts, balance=balance, income_total=income_total, expense_total=expense_total)