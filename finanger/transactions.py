from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .accounts import get_account
from .auth import login_required
from .db import get_db
from .utils import set_date

bp = Blueprint('transactions', __name__, url_prefix='/transactions')


def get_transaction(get_all=False, type=None, year=None, month=None, check_user=False, id=None):

    if get_all:
        zero = ""
        join_acc_destination = ""
        acc_destination = ""
        if month < 10:
            zero = "0"
        if type == "transfers":
            join_acc_destination = "JOIN account ad ON t.account_id_destination = ad.id"
            acc_destination = ", ad.name AS account_destination"

        transactions = get_db().execute(
            f"SELECT t.id, t.description, t.amount, t.date, ao.name AS account_origin{acc_destination} "
            "FROM transactions t "
            "JOIN account ao "
            "ON t.account_id_origin = ao.id "
            f"{join_acc_destination} "
            "JOIN transaction_type tt "
            "ON t.type_id = tt.id "
            "WHERE tt.type = ? "
            "AND strftime('%Y', t.date) = ? "
            "AND strftime('%m', t.date) = ? "
            "AND ao.user_id = ? "
            "ORDER BY t.date DESC ", (type, str(year), f"{zero}{month}", g.user['id'])
        ).fetchall()

        return transactions

    if check_user:
        transaction = get_db().execute(
            'SELECT t.id, t.description, t.amount, t.date, t.account_id_origin, t.account_id_destination, tt.type, a.user_id '
            'FROM transactions t '
            'JOIN transaction_type tt '
            'ON t.type_id = tt.id '
            'JOIN account a '
            'ON t.account_id_origin = a.id '
            'WHERE t.id = ?', (id,)
        ).fetchone()

        if transaction is None:
            abort(404, f"Account id {id} doesn't exist.")

        if transaction['user_id'] != g.user['id']:
            abort(403)
        
        return transaction


@bp.route('/<int:year>/<int:month>')
@login_required
def all(year, month):
    if month < 1 or month > 12:
        return redirect(url_for('.all', year=set_date(year, month)["year"], month=set_date(year, month)['month']))
    
    zero = ""
    if month < 10:
        zero = "0"

    transactions = get_db().execute(
            "SELECT t.id, t.description, t.amount, t.date, a.name AS account, tt.type "
            "FROM transactions t "
            "JOIN transaction_type tt "
            "ON t.type_id = tt.id "
            "JOIN account a "
            "ON t.account_id_origin = a.id "
            "WHERE strftime('%Y', t.date) = ? "
            "AND strftime('%m', t.date) = ? "
            "AND a.user_id = ? "
            "ORDER BY t.date DESC", (str(year), f"{zero}{month}", g.user['id'])
        ).fetchall()

    return render_template('transactions/all.html', transactions=transactions, year=year, month=month)


@bp.route('/<string:type>/<int:year>/<int:month>')
@login_required
def main(type, year, month):
    if type not in ['incomes', 'expenses']:
        return abort(404)
    if month < 1 or month > 12:
        return redirect(url_for('.main', type=type, year=set_date(year, month)["year"], month=set_date(year, month)['month']))

    transactions = get_transaction(get_all=True, type=type, year=year, month=month)

    return render_template('transactions/main.html', transactions=transactions, type=type, year=year, month=month, type_cap=type.capitalize())


@bp.route('/<string:type>/add', methods=('GET', 'POST'))
@login_required
def add(type):
    if type not in ['incomes', 'expenses']:
        return abort(404)

    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        date = request.form['date']
        account = get_account(check_owner=True, id=request.form['account_id'])
        
        error = None

        if not description:
            error = 'Description is required.'
        elif not amount:
            error = 'Amount is required.'
        elif not date:
            error = 'Date is required.'
        elif type == 'expenses' and account['amount'] < amount:
            error = 'Insufficient cash.'

        if error is None:
            if type == 'incomes':
                operator = '+'
                type_id = 1
            elif type == 'expenses':
                operator = '-'
                type_id = 2

            db = get_db()
            db.execute(
                'UPDATE account '
               f'SET amount = amount {operator} ? '
                'WHERE id = ?', (amount, account['id'])
            )
            db.commit()
            
            db.execute(
                'INSERT INTO transactions (description, amount, date, type_id, account_id_origin) '
                'VALUES (?, ?, ?, ?, ?)', (description, amount, date, type_id, account['id'])
            )
            db.commit()

            flash("Transaction added successfully!", "success")
            
            return redirect(url_for('.main', type=type, year=g.date['year'], month=g.date['month']))

        flash(error, "danger")

    accounts = get_account(get_all=True)
    type = type[:-1].capitalize()

    return render_template('transactions/add.html', accounts=accounts, type=type)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    transaction = get_transaction(check_user=True, id=id)
    account = get_account(check_owner=True, id=transaction['account_id_origin'])

    if request.method == 'POST':
        new_description = request.form['description']
        new_amount = float(request.form['amount'])
        new_date = str(request.form['date'])

        error = None

        if not new_description:
            error = 'Description is required.'
        elif not new_amount:
            error = 'Amount is required.'
        elif not new_date:
            error = 'Date is required.'
        elif transaction['type'] == 'expenses' and new_amount > account['amount']:
            error = 'Insufficient Cash.'

        if error is None:
            if transaction['type'] == 'incomes':
                operator = '+'
            elif transaction['type'] == 'expenses':
                operator = '-'
            difference = new_amount - transaction['amount']

            db = get_db()
            db.execute(
                'UPDATE account '
               f'SET amount = amount {operator} ? '
                'WHERE id = ?', (difference, transaction['account_id_origin'])
            )
            db.commit()
            db.execute(
                'UPDATE transactions '
                'SET description = ?, '
                '    amount = ?, '
                '    date = ? '
                'WHERE id = ?', (new_description, new_amount, new_date, id)
            )
            db.commit()

            flash("Transaction updated successfully!", "success")

            return redirect(url_for('.main', type=transaction['type'], year=g.date['year'], month=g.date['month']))

        flash(error, "danger")

    type = transaction['type'][:-1].capitalize()

    return render_template('transactions/update.html', transaction=transaction, type=type, account=account)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    transaction = get_transaction(check_user=True, id=id)

    if transaction['type'] == 'incomes':
        operator = '-'
    elif transaction['type'] == "expenses":
        operator = '+'
    
    db = get_db()
    db.execute(
        'UPDATE account '
       f'SET amount = amount {operator} ? '
        'WHERE id = ?', (transaction['amount'], transaction['account_id_origin'],)
    )
    db.commit()
    db.execute('DELETE FROM transactions WHERE id = ?', (id,))
    db.commit()

    flash("Transaction deleted successfully!", "success")

    return redirect(url_for('transactions.main', type=transaction['type'], year=g.date['year'], month=g.date['month']))