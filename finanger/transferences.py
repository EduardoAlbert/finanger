from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from finanger.accounts import get_account
from finanger.auth import login_required
from finanger.db import get_db

bp = Blueprint('transferences', __name__, url_prefix='/transactions/transferences')


def get_transference(get_all=False, id=None, check_user=False):

    if get_all:
        transferences = get_db().execute(
            "SELECT t.id, t.description, t.amount, t.date, ao.name AS account_origin, ad.name AS account_destination FROM transferences t "
            "JOIN account ao ON t.account_id_origin = ao.id "
            "JOIN account ad ON t.account_id_destination = ad.id "
            "WHERE ao.user_id = ?", (g.user['id'],)
        ).fetchall()

        return transferences

    if check_user:
        transference = get_db().execute(
            'SELECT t.amount, t.account_id_origin, t.account_id_destination, a.user_id '
            'FROM transferences t '
            'JOIN account a '
            'ON t.account_id_origin = a.id '
            'WHERE t.id = ?', (id,)
        ).fetchone()

        if transference is None:
            abort(404, f"Account id {id} doesn't exist.")

        if transference['user_id'] != g.user['id']:
            abort(403)
        
        return transference


def transfer(amount, account_id_origin, account_id_destination, reverse=False):
    db = get_db()

    if reverse:
        aux = account_id_origin
        account_id_origin = account_id_destination
        account_id_destination = aux

    db.execute(
        'UPDATE account '
        'SET amount = amount - ? '
        'WHERE id = ?', (amount, account_id_origin)
    )
    db.commit()

    db.execute(
        'UPDATE account '
        'SET amount = amount + ? '
        'WHERE id = ?', (amount, account_id_destination)
    )
    db.commit()


@bp.route('/')
@login_required
def main():
    transferences = get_transference(get_all=True)

    return render_template('transferences/main.html', transferences=transferences)


@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        date = request.form['date']
        account_id_origin = request.form['account_id_origin']
        account_id_destination = request.form['account_id_destination']
        account_origin = get_account(id=account_id_origin, check_owner=True)
        get_account(id=account_id_destination, check_owner=True)
        error = None

        if not description:
            error = 'Description is required.'
        elif not amount:
            error = 'Amount is required.'
        elif not date:
            error = 'Date is required.'
        elif amount > account_origin['amount']:
            error = 'Insufficient cash.'

        if error is None:
            transfer(amount, account_id_origin, account_id_destination)

            db = get_db()
            db.execute(
                'INSERT INTO '
                'transferences (description, amount, date, account_id_origin, account_id_destination) '
                'VALUES (?, ?, ?, ?, ?)', (description, amount, date, account_id_origin, account_id_destination)
            )
            db.commit()

            return redirect(url_for('transferences.main'))

        flash(error)

    accounts = get_account(get_all=True)

    return render_template('transferences/add.html', accounts=accounts)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    transference = get_transference(id=id, check_user=True)
    transfer(transference['amount'], transference['account_id_origin'], transference['account_id_destination'], reverse=True)
    db = get_db()
    db.execute(
        'DELETE FROM transferences WHERE id = ?', (id,)
    )
    db.commit()

    return redirect(url_for('transferences.main'))
