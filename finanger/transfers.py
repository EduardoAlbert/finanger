from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from .transactions import get_transaction
from .accounts import get_account
from .auth import login_required
from .db import get_db
from .utils import set_date

bp = Blueprint('transfers', __name__, url_prefix='/transactions/transfers')


def do_transfer(amount, account_id_origin, account_id_destination, reverse=False):
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


@bp.route('/<int:year>/<int:month>')
@login_required
def main(year, month):
    if month < 1 or month > 12:
        return redirect(url_for('.main', year=set_date(year, month)["year"], month=set_date(year, month)['month']))
    
    transfers = get_transaction(get_all=True, type="transfers", year=year, month=month)

    return render_template('transfers/main.html', transfers=transfers, year=year, month=month)


@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        date = request.form['date']
        account_id_origin = request.form['account_id_origin']
        account_id_destination = request.form['account_id_destination']
        account_origin = get_account(check_owner=True, id=account_id_origin)
        get_account(check_owner=True, id=account_id_destination)

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
            do_transfer(amount, account_id_origin, account_id_destination)

            db = get_db()
            db.execute(
                'INSERT INTO '
                'transactions (description, amount, date, account_id_origin, account_id_destination, type_id) '
                'VALUES (?, ?, ?, ?, ?, ?)', (description, amount, date, account_id_origin, account_id_destination, 3)
            )
            db.commit()

            flash("Transfer added successfully!", "success")

            return redirect(url_for('.main', month=g.date['month'], year=g.date['year']))

        flash(error, "danger")

    accounts = get_account(get_all=True)

    return render_template('transfers/add.html', accounts=accounts)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    transfer = get_transaction(check_user=True, id=id)
    do_transfer(transfer['amount'], transfer['account_id_origin'], transfer['account_id_destination'], reverse=True)
    db = get_db()
    db.execute('DELETE FROM transactions WHERE id = ?', (id,))
    db.commit()

    flash("Transfer deleted successfully!", "success")
    
    return redirect(url_for('.main', month=g.date['month'], year=g.date['year']))