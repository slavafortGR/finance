from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, DateTimeLocalField
from wtforms.validators import DataRequired, EqualTo, NumberRange


class LoginForm(FlaskForm):
    nick_name = StringField('Nick name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    nick_name = StringField('Nick name', validators=[DataRequired()],
                                    render_kw={'placeholder': 'Enter your nickname'})
    password = PasswordField('Password', validators=[DataRequired(message='The password must be at least 8 characters long')],
                             render_kw={'placeholder': 'Create a password of at least 8 characters'})
    confirm_password = PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password',
                                                                                                 message='Passwords must match')])
    submit = SubmitField('Register')


class IncomeForm(FlaskForm):
    year_month = StringField('Year_month', validators=[DataRequired(message='Select year and month')])
    main_income = IntegerField('Main income', validators=[DataRequired(message='Specify your main income'),
            NumberRange(min=0, message='Income cannot be negative')], default=0)
    additional_income = IntegerField('Additional income', validators=[
            DataRequired(message='Please indicate additional income'),
            NumberRange(min=0, message='Income cannot be negative')], default=0)
    submit = SubmitField('Save')

