from flask import Flask, redirect, render_template, flash, url_for, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from pymongo import MongoClient 
from forms import *
from flask_bootstrap import Bootstrap5
from datetime import datetime

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
bootstrap = Bootstrap5(app) 

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MONGO_URI'] = os.getenv('MONGO_URI')

#client = MongoClient(app.config['MONGO_URI'])
client = MongoClient('mongodb://localhost:27017/')
db = client['mojadb']  
collection_users = db['mojikorisnici'] 


login_manager = LoginManager() # central object that handles authentication
login_manager.init_app(app) 
login_manager.login_view = 'login'  # set the route for login page

@login_manager.user_loader
def load_user(email):
    user_data = collection_users.find_one({'email': email})
    if user_data:
        # If user exists in the database, return a User object
        return User(user_data['email'])
    return None

class User(UserMixin): 
    def __init__(self, email):
        self.id = email
    
    @classmethod
    def get(self_class, id): # gets user with given email
        try:
            return self_class(id)
        except Exception:
            return None
     

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit(): #on POST
        email = form.email.data #not request object because we use Flask-WTF to handle form validation 
        password = form.password.data
        existing_user = collection_users.find_one({'email': email})

        if existing_user:
            flash('User already exists! Please log in.', category='warning')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        collection_users.insert_one({
            'email': email, 
            'password': hashed_password
        })
        flash('Registration successful! You can log in now.', category='success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit(): #on POST
        email = form.email.data
        password = form.password.data
        user_data = collection_users.find_one({'email': email})

        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data['email'])
            login_user(user, form.remember_me.data)  # Log in the user with remember option
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('index')
            flash('Login successful!', category='success')
            return redirect(next)
        
        flash('Invalid email or password. Please try again.', category='warning')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', category='info')
    return redirect(url_for('index'))

# @app.route('/profile')
# @login_required
# def profile():
#     # Placeholder for profile page
#     return render_template('profile.html') if os.path.exists('templates/profile.html') else render_template('index.html')

     



@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404
	
@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'), 500