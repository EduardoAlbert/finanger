from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from finanger.auth import login_required
from finanger.db import get_db
from finanger.dashboard import get_accounts

bp = Blueprint('accounts', __name__, url_prefix='/accounts')


@bp.route('/')
@login_required
def main():
    accounts = get_accounts()
    return render_template('accounts/main.html', accounts=accounts)


@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    if request.method == 'POST':
        name = request.form['name']
        amount = request.form['amount']
        db = get_db()
        error = None

        if not name:
            error = 'Name is required.'
        elif not amount:
            error = 'Amount is required.'

        if error is None:
            db.execute(
                'INSERT INTO account (name, amount, user_id)'
                'VALUES (?, ?, ?)', 
                (name, amount, g.user['id'])
            )
            db.commit()
            return redirect(url_for('accounts.main'))

        flash(error)

    return render_template('accounts/add.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    account = get_accounts(get_all=False, id=id, check_owner=True)

    if request.method == 'POST':
        name = request.form['name']
        amount = request.form['amount']
        error = None

        if not name:
            error = 'Name is required.'
        elif not amount:
            error = 'Amount is required.'

        if error is None:
            db = get_db()
            db.execute(
                'UPDATE account SET name = ?, amount = ?'
                'WHERE id = ?',
                (name, amount, id)
            )
            db.commit()
            return redirect(url_for('accounts.main'))

    return render_template('accounts/update.html', account=account)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_accounts(get_all=False, id=id, check_owner=True)
    db = get_db()
    db.execute('DELETE FROM account WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('accounts.main'))