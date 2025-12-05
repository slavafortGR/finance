from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo


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
