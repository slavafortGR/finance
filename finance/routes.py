import functools
from datetime import date

from flask import render_template, redirect, request,url_for, flash, session
from sqlalchemy.sql.functions import current_user

from finance import app, db
from finance.forms import LoginForm, RegistrationForm, IncomeForm
from finance.logger import logger
from finance.models import User, Income
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

        incomes = Income.query.filter_by(user_id=user_id).filter(
            Income.year == current_year,
            Income.month == current_month
        ).all()

        total_main_income = sum(income.main_income for income in incomes)
        total_additional_income = sum(income.additional_income for income in incomes)
        total_income = total_main_income + total_additional_income

        all_incomes = Income.query.filter_by(user_id=user_id).order_by(
            Income.year.desc(),
            Income.month.desc(),
            Income.day.desc()
        ).all()

        return render_template('profile.html',
                               user=user,
                               total_main_income=total_main_income,
                               total_additional_income=total_additional_income,
                               total_income=total_income,
                               incomes=incomes,
                               all_incomes=all_incomes,
                               current_year=current_year,
                               current_month=current_month)
    else:
        flash('You need to log in', 'danger')
        return redirect(url_for('login_user_get'))


@app.route('/income', methods=['GET'])
@log_exceptions
def add_income_get():
    income_form = IncomeForm(request.form)

    if 'user_id' in session:
        return render_template('add_income.html', income_form=income_form)
    flash('You need login', 'danger')
    return redirect(url_for('login_user_get'))


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
        except (ValueError, AttributeError):
            flash('Invalid date format', 'danger')
            return render_template('add_income.html', income_form=income_form)

        new_income = Income(
            user_id=session['user_id'],
            year=year,
            month=month,
            day=day,
            main_income=income_form.main_income.data,
            additional_income=income_form.additional_income.data
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
