from flask import Flask, redirect, render_template, flash, url_for, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from pymongo import MongoClient 
from forms import *
from flask_bootstrap import Bootstrap5
from datetime import datetime
import gridfs
from bson.objectid import ObjectId

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
bootstrap = Bootstrap5(app) 

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.config['DEBUG'] = os.getenv('DEBUG')

client = MongoClient(app.config['MONGO_URI'])
#client = MongoClient('mongodb://localhost:27017/')
#client = MongoClient(os.getenv('MONGODB_CONNECTION_STRING'))
db = client['mojadb']  
collection_users = db['mojikorisnici'] 
collection_posts = db['mojipostovi']
fs = gridfs.GridFS(db)


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

@app.route('/profile')
@login_required
def profile():
    posts = collection_posts.find({'author_email': current_user.get_id()}).sort('_id', -1)
    return render_template('profile.html', posts=posts)

@app.route('/create_post', methods=['GET', 'POST'])
@login_required 
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        image_id = save_image_to_gridfs(request, fs)
        post = {
            'image_id': image_id,
            'caption': form.caption.data,
            'author_email': current_user.get_id(),
            'likes': [],
        }
        collection_posts.insert_one(post)
        flash('Post created successfully!', category='success')
        return redirect(url_for('index'))
    
    return render_template('create_post.html', form=form)


@app.route('/delete/<post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    collection_posts.delete_one({"_id": ObjectId(post_id)})
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/edit/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    form = PostForm()
    post = collection_posts.find_one({"_id": ObjectId(post_id)})

    if request.method == 'GET':
        #form.image =
        form.caption.data = post['caption']
    
    elif form.validate_on_submit():
        update_data = {
            'caption': form.caption.data,
        }
        new_image_id = save_image_to_gridfs(request, fs)
        if new_image_id is not None:
            update_data['image_id'] = new_image_id 

        collection_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": update_data}
        )       
        flash('Post updated successfully!', category='success')
        return redirect(url_for('profile'))
    return render_template('create_post.html', form=form)

@app.route('/like/<post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    user_email = current_user.get_id()
    post = collection_posts.find_one({"_id": ObjectId(post_id)})

    if user_email in post.get('likes', []):      #unlike
        collection_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$pull": {"likes": user_email}}
        )
        flash('Post unliked', 'info')
    else:                                        #like
        collection_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$addToSet": {"likes": user_email}}
        )
        flash('Post liked!', 'success')
    return redirect(url_for('index'))



@app.route('/', methods=['GET', 'POST'])
def index():
    posts = collection_posts.find().sort('_id', -1)  # Fetch posts from the database, sorted by newest first
    return render_template('index.html', posts=posts)


@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404
	
@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'), 500

def save_image_to_gridfs(request, fs):
    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '':
            # Save the file to GridFS
            image_id = fs.put(image, filename=image.filename)
        else:
            image_id = None
    else:
        image_id = None
    return image_id

@app.route('/image/<image_id>')
def get_image_from_gridfs(image_id):
    image = fs.get(ObjectId(image_id))
    return image.read(), 200, {'Content-Type': 'image/jpeg'}