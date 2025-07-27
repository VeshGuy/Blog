from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from webforms import LoginForm, SignupForm, PostForm, SearchForm
from flask_login import UserMixin, LoginManager, login_required, login_user, logout_user, current_user
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename
from uuid import uuid1
import os 

app = Flask(__name__)

# Old SQLite
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
# New MySQL DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Sarvesh12@localhost/our_users'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config['SECRET_KEY'] = 'secret_key'

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    favcol = db.Column(db.String(100), nullable=False)
    # User can have many posts - One to Many Relationship
    # posts = db.relationship('Posts', backref='poster', cascade="all, delete-orphan", lazy=True)
    # Above code deletes all posts of a user, if the user is deleted
    posts = db.relationship('Posts', backref='poster')
    # Now 'poster' refers to 'Posts' Class
    # If we want to get the author details of a Post, then we just call
    # 'poster.name', 'poster.email'
    profile_pic = db.Column(db.String(1000), nullable=True)

    # How to make changes to database structure
    # You should make these changes in the dierctory which contains all these files
    # python -m flask db [OPTIONS] COMMANDS [ARGS]
    # COMMANDS - migrate, upgrade
    # python -m flask db init
    # python -m flask migrate
    # python -m flask upgrade

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    #author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    slug = db.Column(db.String(255))
    # Foreign Key
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # It is 'users.id' not 'Users.id' cause in SQL it is in small case 

@app.route("/")
def disp():
    return "hi"

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard')) 
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=False)
                flash("Login sucessful!")
                return redirect(url_for('dashboard'))
            else:
                flash("Login Failed!")
                return redirect(url_for('login'))

        else:

            flash("New User!")
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out!')
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET','POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard')) 
    form = SignupForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            pic = request.files['profile_pic']
            
            # Get image name
            pic_filename = secure_filename(pic.filename)
            
            # Set UUID
            pic_name = str(uuid1()) + "_" + pic_filename
            # Save the image
            saver = request.files['profile_pic']
            pic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
            pic = pic_name

            user = Users(name=form.username.data, email=form.email.data, password=generate_password_hash(form.password.data), profile_pic=pic, favcol=form.favcol.data)
            db.session.add(user)
            db.session.commit()
            flash('User added Successfully!')
            return redirect(url_for('login'))
        else:
            flash("Usser already exists!")
            form.username.data=''
            form.email.data=''
            form.password.data=''
            form.favcol.data=''
    return render_template('signup.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user = Users.query.filter_by(email = current_user.email).first()
    return render_template('dashboard.html', user=user)

@app.route('/add-blog', methods=['GET', 'POST'])
@login_required
def add_blog():
    form = PostForm()
    if form.validate_on_submit():
        poster = current_user.id
        flash('Not submitted properly')
        posts = Posts(title=form.title.data, content=form.content.data, slug=form.slug.data, poster_id=poster)
        db.session.add(posts)
        db.session.commit()
        flash('Post successfully Added!')
        return redirect(url_for('all_blogs'))
    
    return render_template('add-blog.html', form=form)

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delblog(id):
    post = Posts.query.filter_by(id=id).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('all_blogs'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def updateblog(id):
    form = PostForm()
    post = Posts.query.filter_by(id=id).first()
    if form.validate_on_submit():
        post.title = form.title.data
        post.author = form.author.data
        post.content = form.content.data
        post.slug = form.slug.data
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('all_blogs'))
    return render_template('update-blog.html', form=form, post=post)

@app.route('/all_blog', methods=['GET', 'POST'])
#@login_required
def all_blogs():
    posts = Posts.query.all()
    return render_template('all_blogs1.html', posts=posts, current_user=current_user)

@app.route('/show_blog/<string:slug>/<int:id>', methods=['GET', 'POST'])
@login_required
def show_blog(slug, id):
    post = Posts.query.filter_by(slug=slug, id=id).first()
    return render_template('show_blog.html', post=post)

# Pass stuff to Navbar for new search function
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        # get data from submitted form
        post_searched = form.search.data
        # Query the database
        posts = posts.filter(Posts.content.like('%' + post_searched + '%'))
        posts = posts.order_by(Posts.title).all()
        return render_template('search.html', form=form, searched=post_searched, posts=posts)

# Delete this    
@app.route('/all', methods=['GET', 'POST'])
@login_required
def display():
    users = Users.query.all()
    print(users)
    return render_template('list.html', users=users)

if __name__=='__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)