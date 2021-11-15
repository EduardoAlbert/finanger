from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from finanger.accounts import get_account
from finanger.auth import login_required
from finanger.db import get_db

bp = Blueprint('transactions', __name__, url_prefix='/transactions')


def get_transaction(get_all=False, id=None, check_user=False, type=None):

    if get_all:
        transactions = get_db().execute(
            "SELECT t.id, t.description, t.amount, t.date, a.name AS account FROM transactions t "
            "JOIN transaction_type tt ON t.type_id = tt.id "
            "JOIN account a ON t.account_id = a.id "
            "WHERE tt.type = ? AND a.user_id = ?", (type, g.user['id'])
        ).fetchall()

        return transactions

    if check_user:
        transaction = get_db().execute(
            'SELECT t.id, t.description, t.amount, t.date, t.account_id, tt.type, a.user_id '
            'FROM transactions t '
            'JOIN transaction_type tt '
            'ON t.type_id = tt.id '
            'JOIN account a '
            'ON t.account_id = a.id '
            'WHERE t.id = ?', (id,)
        ).fetchone()

        if transaction is None:
            abort(404, f"Account id {id} doesn't exist.")

        if transaction['user_id'] != g.user['id']:
            abort(403)
        
        return transaction


@bp.route('/<string:type>')
@login_required
def main(type):
    if type not in ['incomes', 'expenses']:
        return abort(404)

    transactions = get_transaction(get_all=True, type=type)

    type = type.capitalize()

    return render_template('transactions/main.html', transactions=transactions, type=type)


@bp.route('/<string:type>/add', methods=('GET', 'POST'))
@login_required
def add(type):
    """Add incomes and expenses"""
    if type not in ['incomes', 'expenses']:
        return abort(404)

    if request.method == 'POST':

        description = request.form['description']
        amount = float(request.form['amount'])
        date = request.form['date']
        account = get_account(id=request.form['account_id'], check_owner=True)
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
            operator = '+'
            type_id = 1
            if type == 'expenses':
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
                'INSERT INTO transactions (description, amount, date, type_id, account_id) '
                'VALUES (?, ?, ?, ?, ?)', (description, amount, date, type_id, account['id'])
            )
            db.commit()

            return redirect(url_for('transactions.main', type=type))

        flash(error)

    accounts = get_account(get_all=True)
    type = type[:-1].capitalize()

    return render_template('transactions/add.html', accounts=accounts, type=type)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    """Update incomes and expenses"""
    transaction = get_transaction(id=id, check_user=True)
    account = get_account(id=transaction['account_id'], check_owner=True)

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
            operator = '+'
            if transaction['type'] == 'expenses':
                operator = '-'
            difference = new_amount - transaction['amount']

            db = get_db()
            db.execute(
                'UPDATE account '
               f'SET amount = amount {operator} ? '
                'WHERE id = ?', (difference, transaction['account_id'])
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

            return redirect(url_for('transactions.main', type=transaction['type']))

        flash(error)

    type = transaction['type'][:-1].capitalize()

    return render_template('transactions/update.html', transaction=transaction, type=type, account=account)

    
@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    transaction = get_transaction(id=id, check_user=True)

    operator = '+'
    if transaction['type'] == 'incomes':
        operator = '-'
    
    db = get_db()
    db.execute(
        'UPDATE account '
       f'SET amount = amount {operator} ? '
        'WHERE id = ?', (transaction['amount'], transaction['account_id'],)
    )
    db.commit()
    db.execute(
        'DELETE FROM transactions '
        'WHERE id = ?', (id,)
    )
    db.commit()

    return redirect(url_for('transactions.main', type=transaction['type']))