from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo



class RegisterForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email(), Length(3, 60)])
    password = PasswordField('Password', validators=[DataRequired(), Length(3, 60), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), Length(3, 30)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email(), Length(3, 60)])
    password = PasswordField('Password', validators=[DataRequired(), Length(3, 30)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

