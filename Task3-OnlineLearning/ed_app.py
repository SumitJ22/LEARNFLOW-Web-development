from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# Configure MySQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:12345@localhost/online_learning'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '6NWMu7ewCqm7GX6tbG0sd532ashdfhasd5dasd21das5OJmU8QNWZ2A5'
app.config['UPLOAD_FOLDER'] = 'static/videos'

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    video_path = db.Column(db.String(255))

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    """ Home Page - Landing Page """
    return render_template("index.html")

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    """ User Registration Page """
    if 'username' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(username=username).first():
            flash('Username already taken. Try another.', 'error')
            return redirect(url_for('sign_up'))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('sign_up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ User Login Page """
    if 'username' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """ Logout Route """
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))

@app.route('/courses')
def courses():
    """ Display all uploaded courses """
    all_courses = Course.query.all()
    user_enrolled_courses = []

    if 'user_id' in session:
        user_id = session['user_id']
        user_enrolled_courses = [e.course_id for e in Enrollment.query.filter_by(user_id=user_id).all()]

    return render_template('course.html', courses=all_courses, user_enrolled_courses=user_enrolled_courses)

@app.route('/newcourse', methods=['GET', 'POST'])
def new_course():
    """ Page for creating new courses (Admin only) """
    if 'username' not in session:
        flash('You must be logged in to add a course.', 'info')
        return redirect(url_for('login'))
    
    if session['username'].lower() != 'admin':  # Restrict access to admin only
        flash('Only admins can add courses.', 'error')
        return redirect(url_for('courses'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        video = request.files['video']

        if video:
            filename = secure_filename(video.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video.save(video_path)  # Save in 'static/videos/'

            new_course = Course(title=title, description=description, video_path=filename)
            db.session.add(new_course)
            db.session.commit()

            flash('Course added successfully!', 'success')
            return redirect(url_for('courses'))

    return render_template('newcourse.html')

@app.route('/enroll/<int:course_id>', methods=['POST'])
def enroll(course_id):
    """ Enroll User in a Course """
    if 'user_id' not in session:
        flash('Please log in to enroll in courses.', 'info')
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    # Check if the user is already enrolled
    existing_enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    if existing_enrollment:
        flash("You are already enrolled in this course.", "info")
        return redirect(url_for('courses'))

    # Add new enrollment
    new_enrollment = Enrollment(user_id=user_id, course_id=course_id)
    db.session.add(new_enrollment)
    db.session.commit()

    flash("Successfully enrolled!", "success")
    return redirect(url_for('courses'))

@app.route('/my_courses')
def my_courses():
    """ Display Courses User is Enrolled In """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    enrolled_courses = db.session.query(Course).join(Enrollment).filter(Enrollment.user_id == user_id).all()

    return render_template('course.html', user_courses=enrolled_courses, courses=None)

if __name__ == '__main__':
    app.run(debug=True)
