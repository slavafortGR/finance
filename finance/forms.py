from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, DateTimeLocalField, \
    TextAreaField
from wtforms.validators import DataRequired, EqualTo, NumberRange, Optional, Length
from finance.models import Category
from finance.validators import NotFutureDate


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
    date = StringField('Date', validators=[DataRequired(message='Select date'),
            NotFutureDate(message='Cannot add income for future dates')])
    main_income = IntegerField('Main income', validators=[Optional(),
            NumberRange(min=0, message='Income cannot be negative')], default=0)
    additional_income = IntegerField('Additional income', validators=[Optional(),
            NumberRange(min=0, message='Income cannot be negative')], default=0)
    comment = TextAreaField("Comment",validators=[Optional(), Length(max=255)])
    submit = SubmitField('Save')


class ExpenseForm(FlaskForm):
    category_id = SelectField('Category', coerce=int, validators=[DataRequired(message='Select category')])
    amount = IntegerField('Amount', validators=[DataRequired(message='Enter amount'),
            NumberRange(min=1, max=1000000, message='Amount must be between 1 and 1,000,000')])
    date = StringField('Date', validators=[DataRequired(message='Select date'),
            NotFutureDate(message='Cannot add expense for future dates')])
    comment = TextAreaField('Comment (optional)',
        validators=[Optional(), Length(max=200, message='Comment cannot exceed 200 characters')])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(ExpenseForm, self).__init__(*args, **kwargs)
        from finance.models import Category
        self.category_id.choices = [
            (c.id, f'{c.icon} {c.display_name}')
            for c in Category.query.order_by(Category.order).all()
        ]
