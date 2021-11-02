from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from finanger.auth import login_required
from finanger.db import get_db

bp = Blueprint('dashboard', __name__)


def get_accounts(get_all=True, id=None, check_owner=False):

    if get_all:
        accounts = get_db().execute(
            'SELECT id, name, amount FROM account WHERE user_id = ?', (g.user['id'],)
        ).fetchall()
        return accounts

    if check_owner:
        account = get_db().execute(
            'SELECT id, name, amount, user_id FROM account WHERE id = ?', (id,)
        ).fetchone()

        if account is None:
            abort(404, f"Account id {id} doesn't exist.")

        if account['user_id'] != g.user['id']:
            abort(403)
        
        return account


@bp.route('/')
@login_required
def index():
    accounts = get_accounts()
    balance = 0
    for account in accounts:
        balance += account['amount']
    return render_template('dashboard/index.html', accounts=accounts, balance=balance)