from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FileField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileAllowed



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

class PostForm(FlaskForm):
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    caption = TextAreaField('Caption', validators=[Length(max=1000)])
    submit = SubmitField('Post')
