import functools

from flask import render_template, redirect, request,url_for, flash, session
from finance import app
from finance.forms import LoginForm, RegistrationForm
from finance.logger import logger
from finance.models import User
from werkzeug.security import check_password_hash


def log_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f'Ошибка в {func.__name__}: {str(e)}', exc_info=True)
            from flask import request
            if request:
                return 'Произошла ошибка на сервере', 500
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

        user = User.query.filter_by(personnel_number=nick_name).first()
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
