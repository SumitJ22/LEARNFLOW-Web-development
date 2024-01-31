from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session, g, flash
import sqlite3
import os 
from werkzeug.utils import secure_filename




app = Flask(__name__)
app.config['DATABASE'] = 'edtech.db'
app.secret_key = '6NWMu7ewCqm7GX6tbG0sd532ashdfhasd5dasd21das5OJmU8QNWZ2A5'
app.config['UPLOAD_FOLDER'] = 'static/videos'



def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    result = cur.fetchall()
    cur.close()
    column_names = [column[0] for column in cur.description]

    if not result:
        return None

    if one:
        return dict(zip(column_names, result[0]))

    return [dict(zip(column_names, row)) for row in result]





with app.app_context():
    init_db()



@app.route('/')
def home():
    return render_template("index.html")

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if 'username' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
           
            

            db = get_db()
            db.execute('INSERT INTO Users (username, password, email) VALUES (?, ?, ?)',
                       (username, password, email))
            db.commit()
            

            flash('You were successfully registered', 'success')
            return redirect(url_for('login'))

    return render_template('sign_up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = query_db('SELECT * FROM Users WHERE username = ?', [username], one=True)

        if user and user['password'] == password:
          
            session['username'] = user['username']
            session['user_id'] = user['id']
            flash('You were successfully logged in', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You were logged out', 'info')
    return redirect(url_for('home'))


@app.route('/courses')
def courses():
    db = get_db()
    courses = query_db('SELECT * FROM Courses')
    return render_template('course.html', courses=courses)


@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        content = request.form['content']

        video = request.files['video']
        if video:
            filename = secure_filename(video.filename)
            video_path = os.path.join('videos', filename)
            video.save(os.path.join(app.root_path, 'static', video_path)) 

          
            db = get_db()
            db.execute('INSERT INTO Courses (title, description, content, creator_id, link) VALUES (?, ?, ?, ?, ?)',
                       (title, description, content, session.get('id'), video_path.replace('\\', '/')))
            db.commit()

            flash('New course added successfully', 'success')
            return redirect(url_for('courses'))
    return render_template('newcourse.html')


@app.route('/enroll', methods=['POST'])
def enroll():
    if 'user_id' not in session:
        flash('Please log in to enroll in courses', 'info')
        return redirect(url_for('login'))

    user_id = session['user_id']
    course_id = request.form.get('course_id')

    db = get_db()

    existing_enrollment = query_db('SELECT * FROM Enrollments WHERE user_id = ? AND course_id = ?',
                                   (user_id, course_id), one=True)
    if existing_enrollment:
        flash('You are already enrolled in this course', 'info')
        return redirect(url_for('courses'))

 
    try:
        db.execute('INSERT INTO Enrollments (user_id, course_id, progress) VALUES (?, ?, 0)',
                   (user_id, course_id))
        db.commit()
        flash('Successfully enrolled in the course', 'success')
        return redirect(url_for('courses', enrolled=True))
    except sqlite3.IntegrityError as e:
        flash('An error occurred while enrolling in the course', 'error')
        return redirect(url_for('courses'))

    return redirect(url_for('courses'))


if __name__ == '__main__':
    app.run(debug=True)