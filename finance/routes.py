import functools
from datetime import datetime, date, timedelta
from itertools import groupby
import json

from flask import render_template, redirect, request,url_for, flash, session
from sqlalchemy.sql.functions import current_user
from sqlalchemy import func, extract

from finance import app, db
from finance.forms import LoginForm, RegistrationForm, IncomeForm, ExpenseForm
from finance.logger import logger
from finance.models import User, Income, Expense, Category
from werkzeug.security import check_password_hash, generate_password_hash



def log_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f'Error in {func.__name__}: {str(e)}', exc_info=True)
            from flask import request
            if request:
                return 'An error occurred on the server', 500
            else:
                raise

    return wrapper


@app.route('/')
@log_exceptions
def return_main_page():
    return render_template('main_page.html')


@app.route('/login', methods=['GET'])
@log_exceptions
def login_user_get():
    login_form = LoginForm(request.form)
    return render_template('login_register.html', login_tab=True, login_form=login_form)


@app.route('/login', methods=['POST'])
@log_exceptions
def login_user_post():
    login_form = LoginForm(request.form)

    if login_form.validate_on_submit():
        nick_name = login_form.nick_name.data
        password = login_form.password.data

        user = User.query.filter_by(nick_name=nick_name).first()
        if not user or not check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_nick'] = user.nick_name
            flash('Incorrect login or password', 'danger')
            return redirect(url_for('login_user_get'))
        else:
            session['user_id'] = user.id
            return redirect(url_for('return_profile'))

    flash('Incorrect data entry. Please check and re-enter.', 'danger')
    return redirect(url_for('login_user_get'))


@app.route('/register', methods=['GET'])
@log_exceptions
def register_user_get():
    registration_form = RegistrationForm(request.form)
    return render_template('login_register.html', register_tab=True, registration_form=registration_form)


@app.route('/register', methods=['POST'])
@log_exceptions
def register_user_post():
    registration_form = RegistrationForm(request.form)

    if registration_form.validate_on_submit():
        nick_name = registration_form.nick_name.data
        password = registration_form.password.data

        # if not validate_register_form(personnel_number, password):
        #     return render_template('login_register.html', register_tab=True, registration_form=registration_form)

        if User.query.filter_by(nick_name=nick_name).first() is not None:
            flash('This nickname already exists', 'danger')
            return render_template('login_register.html', register_tab=True, registration_form=registration_form)

        new_user = User(
            nick_name=nick_name,
            password=generate_password_hash(password)
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            flash('You have successfully registered.', 'success')
            return redirect(url_for('login_user_get'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    else:
        flash('Incorrect registration data', 'danger')
        return render_template('login_register.html', register_tab=True, registration_form=registration_form)


@app.route('/logout')
@log_exceptions
def logout():
    session.pop('user_id', None)
    return redirect(url_for('return_main_page'))


@app.route('/profile', methods=['GET'])
@log_exceptions
def return_profile():
    user_id = session.get('user_id')

    if user_id:
        user = User.query.filter_by(id=user_id).first()

        current_date = date.today()
        current_year = current_date.year
        current_month = current_date.month

        all_incomes = Income.query.filter_by(user_id=user_id).order_by(
            Income.year.desc(),
            Income.month.desc(),
            Income.day.asc()
        ).all()

        all_expenses = Expense.query.filter_by(user_id=user_id).all()

        monthly_incomes = {}
        for key, group in groupby(all_incomes, key=lambda x: (x.year, x.month)):
            year, month = key
            month_key = f'{year}-{month:02d}'
            income_list = list(group)

            total_main = sum(inc.main_income for inc in income_list)
            total_additional = sum(inc.additional_income for inc in income_list)
            total = total_main + total_additional

            monthly_incomes[month_key] = {
                'incomes': income_list,
                'total_main': total_main,
                'total_additional': total_additional,
                'total': total,
                'year': year,
                'month': month
            }

        monthly_expenses = {}
        for expense in all_expenses:
            month_key = f'{expense.date.year}-{expense.date.month:02d}'
            if month_key not in monthly_expenses:
                monthly_expenses[month_key] = 0
            monthly_expenses[month_key] += expense.amount

        for month_key in monthly_incomes:
            expenses_total = monthly_expenses.get(month_key, 0)
            monthly_incomes[month_key]['expenses'] = expenses_total
            monthly_incomes[month_key]['balance'] = monthly_incomes[month_key]['total'] - expenses_total

        current_month_key = f'{current_year}-{current_month:02d}'
        if current_month_key in monthly_incomes:
            current_month_data = monthly_incomes[current_month_key]
            total_main_income = current_month_data['total_main']
            total_additional_income = current_month_data['total_additional']
            total_income = current_month_data['total']
            total_expenses = current_month_data['expenses']
            balance = current_month_data['balance']
        else:
            total_main_income = 0
            total_additional_income = 0
            total_income = 0
            total_expenses = monthly_expenses.get(current_month_key, 0)
            balance = total_income - total_expenses

        return render_template('profile.html',
                               user=user,
                               total_main_income=total_main_income,
                               total_additional_income=total_additional_income,
                               total_income=total_income,
                               total_expenses=total_expenses,
                               balance=balance,
                               monthly_incomes=monthly_incomes,
                               current_year=current_year,
                               current_month=current_month)
    else:
        flash('You need to log in', 'danger')
        return redirect(url_for('login_user_get'))


@app.route('/income', methods=['GET'])
@log_exceptions
def add_income_get():
    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    income_form = IncomeForm()
    return render_template('add_income.html',
                           income_form=income_form,
                           today=date.today().isoformat())


@app.route('/income', methods=['POST'])
@log_exceptions
def add_income_post():

    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    income_form = IncomeForm(request.form)

    if income_form.validate_on_submit():
        date_str = income_form.date.data

        try:
            year, month, day = date_str.split('-')
            year = int(year)
            month = int(month)
            day = int(day)

            input_date = date(year, month, day)
            if input_date > date.today():
                flash('Cannot add income for future dates', 'danger')
                return render_template('add_income.html', income_form=income_form)

        except (ValueError, AttributeError):
            flash('Invalid date format', 'danger')
            return render_template('add_income.html', income_form=income_form)

        main_income = income_form.main_income.data or 0
        additional_income = income_form.additional_income.data or 0

        if main_income == 0 and additional_income == 0:
            flash('At least one income field must be filled', 'danger')
            return render_template('add_income.html', income_form=income_form)

        new_income = Income(
            user_id=session['user_id'],
            year=year,
            month=month,
            day=day,
            main_income=main_income,
            additional_income=additional_income,
            comment=income_form.comment.data.strip() or None
        )

        try:
            db.session.add(new_income)
            db.session.commit()

            flash('Income successfully added', 'success')
            return redirect(url_for('return_profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return render_template('add_income.html', income_form=income_form)
    else:
        flash('Incorrect income data', 'danger')
        return render_template('add_income.html', income_form=income_form)


@app.route('/income/<int:income_id>/edit', methods=['GET'])
@log_exceptions
def edit_income_get(income_id):
    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    income = Income.query.get_or_404(income_id)

    if income.user_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('return_profile'))

    income_form = IncomeForm()
    income_form.date.data = f'{income.year}-{income.month:02d}-{income.day:02d}'
    income_form.main_income.data = income.main_income
    income_form.additional_income.data = income.additional_income

    return render_template('edit_income.html', income_form=income_form, income=income)


@app.route('/income/<int:income_id>/edit', methods=['POST'])
@log_exceptions
def edit_income_post(income_id):
    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    income = Income.query.get_or_404(income_id)

    if income.user_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('return_profile'))

    income_form = IncomeForm(request.form)

    if income_form.validate_on_submit():
        date_str = income_form.date.data

        try:
            year, month, day = date_str.split('-')
            year = int(year)
            month = int(month)
            day = int(day)
        except (ValueError, AttributeError):
            flash('Invalid date format', 'danger')
            return render_template('edit_income.html', income_form=income_form, income=income)

        main_income = income_form.main_income.data or 0
        additional_income = income_form.additional_income.data or 0

        if main_income == 0 and additional_income == 0:
            flash('At least one income field must be filled', 'danger')
            return render_template('edit_income.html', income_form=income_form, income=income)

        income.year = year
        income.month = month
        income.day = day
        income.main_income = main_income
        income.additional_income = additional_income
        income.comment = income_form.comment.data.strip() or None

        try:
            db.session.commit()
            flash('Income updated successfully', 'success')
            return redirect(url_for('return_profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return render_template('edit_income.html', income_form=income_form, income=income)
    else:
        flash('Incorrect income data', 'danger')
        return render_template('edit_income.html', income_form=income_form, income=income)


@app.route('/income/<int:income_id>/delete', methods=['POST'])
@log_exceptions
def delete_income(income_id):
    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    income = Income.query.get_or_404(income_id)

    if income.user_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('return_profile'))

    try:
        db.session.delete(income)
        db.session.commit()
        flash('Income deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('return_profile'))


@app.route('/expense', methods=['GET'])
@log_exceptions
def add_expense_get():
    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    expense_form = ExpenseForm()
    return render_template('add_expense.html',
                           expense_form=expense_form,
                           today=date.today().isoformat())


@app.route('/expense', methods=['POST'])
@log_exceptions
def add_expense_post():
    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    expense_form = ExpenseForm(request.form)

    if expense_form.validate_on_submit():
        try:
            expense_date = datetime.strptime(expense_form.date.data, '%Y-%m-%d').date()

            if expense_date > date.today():
                flash('Cannot add expense for future dates', 'danger')
                return render_template('add_expense.html', expense_form=expense_form)

        except ValueError:
            flash('Invalid date format', 'danger')
            return render_template('add_expense.html', expense_form=expense_form)

        new_expense = Expense(
            user_id=session['user_id'],
            category_id=expense_form.category_id.data,
            amount=expense_form.amount.data,
            date=expense_date,
            comment=expense_form.comment.data.strip() or None
        )

        try:
            db.session.add(new_expense)
            db.session.commit()
            flash('Expense successfully added', 'success')
            return redirect(url_for('list_expenses'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return render_template('add_expense.html', expense_form=expense_form)
    else:
        flash('Incorrect expense data', 'danger')
        return render_template('add_expense.html', expense_form=expense_form)


@app.route('/expenses', methods=['GET'])
@log_exceptions
def list_expenses():
    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    expenses = Expense.query.filter_by(
        user_id=session['user_id']
    ).order_by(Expense.date.desc()).all()

    from itertools import groupby

    monthly_expenses = {}
    for key, group in groupby(expenses, key=lambda x: (x.date.year, x.date.month)):
        year, month = key
        monthly_expenses[f'{year}-{month:02d}'] = list(group)

    return render_template('list_expenses.html', monthly_expenses=monthly_expenses)


@app.route('/expense/<int:expense_id>/edit', methods=['GET'])
@log_exceptions
def edit_expense_get(expense_id):
    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('list_expenses'))

    expense_form = ExpenseForm(obj=expense)
    expense_form.date.data = expense.date.isoformat()

    return render_template('edit_expense.html', expense_form=expense_form, expense=expense)


@app.route('/expense/<int:expense_id>/edit', methods=['POST'])
@log_exceptions
def edit_expense_post(expense_id):
    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('list_expenses'))

    expense_form = ExpenseForm(request.form)

    if expense_form.validate_on_submit():
        try:
            expense_date = datetime.strptime(expense_form.date.data, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'danger')
            return render_template('edit_expense.html', expense_form=expense_form, expense=expense)

        expense.category_id = expense_form.category_id.data
        expense.amount = expense_form.amount.data
        expense.date = expense_date
        expense.comment = expense_form.comment.data.strip() or None

        try:
            db.session.commit()
            flash('Expense updated successfully', 'success')
            return redirect(url_for('list_expenses'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return render_template('edit_expense.html', expense_form=expense_form, expense=expense)
    else:
        flash('Incorrect expense data', 'danger')
        return render_template('edit_expense.html', expense_form=expense_form, expense=expense)


@app.route('/expense/<int:expense_id>/delete', methods=['POST'])
@log_exceptions
def delete_expense(expense_id):
    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('list_expenses'))

    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('list_expenses'))


@app.route('/statistics', methods=['GET'])
@log_exceptions
def statistics():
    if 'user_id' not in session:
        flash('You need login', 'danger')
        return redirect(url_for('login_user_get'))

    user_id = session['user_id']

    current_date = date.today()
    months_data = []

    for i in range(5, -1, -1):
        target_date = current_date.replace(day=1) - timedelta(days=30 * i)
        year = target_date.year
        month = target_date.month

        incomes = Income.query.filter_by(
            user_id=user_id,
            year=year,
            month=month
        ).all()

        total_income = sum(inc.total for inc in incomes)

        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month
        ).all()

        total_expenses = sum(exp.amount for exp in expenses)

        months_data.append({
            'month': f"{year}-{month:02d}",
            'month_name': target_date.strftime('%B %Y'),
            'income': total_income,
            'expenses': total_expenses,
            'balance': total_income - total_expenses
        })

    three_months_ago = current_date - timedelta(days=90)

    expenses_by_category = db.session.query(
        Category.display_name,
        Category.icon,
        func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        Expense.user_id == user_id,
        Expense.date >= three_months_ago
    ).group_by(Category.display_name, Category.icon).order_by(
        func.sum(Expense.amount).desc()
    ).all()

    all_categories = [
        {
            'display_name': row[0],
            'icon': row[1],
            'total': row[2]
        }
        for row in expenses_by_category
    ]

    top_categories = all_categories[:5]

    total_income_all = db.session.query(func.sum(Income.main_income + Income.additional_income)).filter(
        Income.user_id == user_id
    ).scalar() or 0

    total_expenses_all = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id
    ).scalar() or 0

    return render_template('statistics.html',
                           months_data=months_data,
                           top_categories=top_categories,
                           all_categories=all_categories,
                           total_income_all=total_income_all,
                           total_expenses_all=total_expenses_all,
                           balance_all=total_income_all - total_expenses_all)
