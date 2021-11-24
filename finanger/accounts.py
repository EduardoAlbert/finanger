from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from finanger.auth import login_required
from finanger.db import get_db

bp = Blueprint('accounts', __name__, url_prefix='/accounts')


def get_account(get_all=False, id=None, check_owner=False):

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
def main():
    accounts = get_account(get_all=True)
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

            flash("Account added successfully!", "success")

            return redirect(url_for('accounts.main'))

        flash(error, "danger")

    return render_template('accounts/add.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    account = get_account(id=id, check_owner=True)

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

            flash("Account updated successfully!", "success")

            return redirect(url_for('accounts.main'))
        
        flash(error, "danger")

    return render_template('accounts/update.html', account=account)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_account(id=id, check_owner=True)
    db = get_db()
    db.execute('DELETE FROM account WHERE id = ?', (id,))
    db.commit()
    flash("Account deleted successfully!", "success")
    return redirect(url_for('accounts.main'))