from flask import Flask, flash, redirect, request, render_template, url_for, session
from flask_sslify import SSLify
import secrets
import sqlite3
import json
import sys

# Setup
app = Flask(__name__, static_url_path='/static')
sslify = SSLify(app)
random = secrets.token_urlsafe(16)
app.config['SECRET_KEY'] = random

# Flask app
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Login details from user
        username = request.form['username']
        password = request.form['password']

        # Get the user's type (doctor or patient here) and redirect to the appropriate page
        with sqlite3.connect('app.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT type FROM users WHERE username = (?)", (username,))
            rows = cur.fetchall()

        try:
            type = rows[0]['type']
        except IndexError:
            flash("User doesn't exist - create an account first", 'alert alert-dismissible alert-danger')
            return redirect(url_for('signup'))

        # Check password
        with sqlite3.connect('app.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT password FROM users WHERE username = (?)", (username,))
            rows = cur.fetchall()

        db_password = rows[0]['password']

        # Check if details match
        if db_password == password:
            check = True
        else:
            check = False

        if check:
            if type == "doctor":
                # Pull from db if the user has confirmed details
                with sqlite3.connect('app.db') as con:
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute("SELECT quiz FROM users WHERE username = (?)", (username,))
                    rows = cur.fetchall()

                details = rows[0]['quiz']
                if details == "true":
                    session['details'] = True
                else:
                    session['details'] = False

                # Set cookies, log in as doctor
                session['username'] = username
                session['type'] = "doctor"

                flash('You are now logged in as a doctor.', 'alert alert-dismissible alert-success')
                return redirect(url_for('doctor'))
            else:
                with sqlite3.connect('app.db') as con:
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute("SELECT quiz FROM users WHERE username = (?)", (username,))
                    rows = cur.fetchall()

                details = rows[0]['quiz']

                if details == "true":
                    session['details'] = True
                else:
                    session['details'] = False

                # Set cookies, log in as patient
                session['username'] = username
                session['type'] = "patient"

                flash('You are now logged in as a patient.', 'alert alert-dismissible alert-success')
                return redirect(url_for('user'))
        else:
            flash('Invalid login details.', 'alert alert-dismissible alert-danger')
            return redirect(url_for('login'))

    else:
        if session.get('username'):
            if session.get('type') == "doctor":
                return redirect(url_for('doctor'))
            else:
                return redirect(url_for('user'))
        return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Signup details from user
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Doctor or patient
        user_type = request.form['options']

        # Check with the db if account exists, if not create account
        with sqlite3.connect('app.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT type FROM users WHERE username = (?)", (username,))
            rows = cur.fetchall()

        if len(rows) != 0:
            flash('Account already exists, choose a different username.', 'alert alert-dismissible alert-danger')
            return redirect(url_for('signup'))

        # Create account with db here

        with sqlite3.connect('app.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("INSERT INTO users(username, email, password, type, quiz) VALUES (?, ?, ?, ?, ?)", (username, email, password, user_type, "false"))
            con.commit()

        flash('Account created! Please log in.', 'alert alert-dismissible alert-success')
        return redirect(url_for('login'))

    else:
        return render_template('signup.html')


# Home page after patient logs in
# Patient can take the test, view the available doctors or their results from the last time
@app.route('/user', methods=['GET'])
def user():
    if session.get('username'):
        username = session['username']
        if session.get('type') == "patient":
            if session.get('details'):
                # Get patient details from db
                with sqlite3.connect('app.db') as con:
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute("SELECT name, email, location, age, gender, diseases, additional FROM users WHERE username = (?)", (username,))
                    rows = cur.fetchall()

                rows = rows[0]

                diseases = rows['diseases']
                if diseases != None:
                    diseases = json.loads(diseases)
                else:
                    diseases = {'Test not taken yet': '100'}

                patient ={
                    'name': rows['name'],
                    'email': rows['email'],
                    'location': rows['location'],
                    'age': rows['age'],
                    'gender': rows['gender'],
                    'diseases': diseases,
                    'add': rows['additional']
                }

                # patient ={
                #     'name': 'John',
                #     'email': 'john@email.com',
                #     'location': 'tokyo',
                #     'age': '25',
                #     'gender': 'male',
                #     'diseases': {'common flu': '90', 'cancer': '30'},
                #     'add' : 'whatever they wanna add'
                #     }
                return render_template('user.html', username=username, patient=patient)
            else:
                # They haven't filled in the quiz
                return redirect(url_for('quiz'))
        else:
            # Somehow doctor got to user page
            flash("Oops! We'll be logging you in to the appropriate page now.", 'alert alert-dismissible alert-danger')
            return redirect(url_for('doctor'))
    else:
        # Haven't logged in
        flash('Log in first', 'alert alert-dismissible alert-danger')
        return redirect(url_for('login'))


# Home page after doctor logs in
# Here they can see patients and their details, likely diseases etc.
@app.route('/doctor', methods=['GET'])
def doctor():
    if session.get('username'):
        username = session['username']
        if session.get('type') == "doctor":
            if session.get('details'):

                with sqlite3.connect('app.db') as con:
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute("SELECT name, email, location, school, education, age, gender, skills, additional, likes, dislikes FROM users WHERE username = (?)", (username,))
                    rows = cur.fetchall()

                rows = rows[0]

                skills_un = rows['skills']
                # Parse
                skills = skills_un.split(",")

                doctor = {
                    'name': rows['name'],
                    'email': rows['email'],
                    'location': rows['location'],
                    'school': rows['school'],
                    'education': rows['education'],
                    'age': rows['age'],
                    'gender': rows['gender'],
                    'skills': skills,
                    'add' : rows['additional'],
                    'likes': rows['likes'],
                    'dislikes' : rows['dislikes']
                }

                return render_template('doctor.html', doctor=doctor, username=username)
            else:
                return redirect(url_for('quiz'))
        else:
            # Somehow user got to doctor page
            flash("Oops! We'll be logging you in to the appropriate page now.", 'alert alert-dismissible alert-danger')
            return redirect(url_for('user'))
    else:
        # Haven't logged in
        flash('Log in first', 'alert alert-dismissible alert-danger')
        return redirect(url_for('login'))

# User / doctor fills in more details
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        if session.get('type') == "doctor":
            username = session.get('username')

            name = request.form['name']
            location = request.form['location']
            school = request.form['school']
            age = request.form['age']
            gender = request.form['gender']
            add = request.form['add']

            skills = request.form['skills']

            education = request.form['education']

            session['details'] = True

            with sqlite3.connect('app.db') as con:
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                cur.execute("UPDATE users SET name=(?), location=(?), school=(?), age=(?), gender=(?), additional=(?), skills=(?), education=(?), quiz=(?) WHERE username=(?)", (name, location, school, age, gender, add, skills, education, "true", username))
                con.commit()

            flash('Thank you!', 'alert alert-dismissible alert-success')
            return redirect(url_for('doctor'))
        else:
            username = session.get('username')
            name = request.form['name']
            location = request.form['location']
            age = request.form['age']
            gender = request.form['gender']
            add = request.form['add']

            with sqlite3.connect('app.db') as con:
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                cur.execute("UPDATE users SET name=(?), location=(?), age=(?), gender=(?), additional=(?), quiz=(?) WHERE username=(?)", (name, location, age, gender, add, "true", username))
                con.commit()

            session['details'] = True

            flash('Thank you!', 'alert alert-dismissible alert-success')
            return redirect(url_for('user'))


    else:
        if session.get('type') == "doctor":
            return render_template('doctor_quiz.html')
        else:
            return render_template('patient_quiz.html')

# Chatbot / quiz things
# Pass final results in a dict
# Eg. diseases = {'common flu': '90', 'cancer': '30'}
@app.route('/evaluate', methods =["GET", "POST"])
def evaluate():
    if request.method == "POST":
        username = session.get('username')
        # Add their likely diseases to the db
        diseases = {'common flu': '90', 'cancer': '30'}
        with sqlite3.connect('app.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("UPDATE users SET diseases=(?) WHERE username=(?)", (json.dumps(diseases), username))
            con.commit()
        return render_template('results.html')
    else:
        if session.get('username'):
            return render_template('evaluate.html')
        else:
            # Haven't logged in
            flash('Log in first', 'alert alert-dismissible alert-danger')
            return redirect(url_for('login'))

# Contains the doctors so the users can see who is available
# Pass results in a list of dicts
@app.route('/doctors', methods=['GET', 'POST'])
def doctors():
    if request.method == 'POST':
        search_un = request.form['search']
        # Get the doctors from the db where criteria meets search
        with sqlite3.connect('app.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            search = '%'+search_un+'%'
            cur.execute("SELECT name, email, location, school, education, age, gender, skills, additional, likes, dislikes FROM users WHERE name LIKE (?) OR school LIKE (?) OR education LIKE (?) OR gender LIKE (?) OR skills LIKE (?) OR additional LIKE (?) OR username LIKE (?)", (search, search, search, search, search, search, search))
            rows = cur.fetchall()

        doctors = []

        for row in rows:
            skills_un = row['skills']
            # Parse
            skills = skills_un.split(",")
            doctor = {
                'name': row['name'],
                'email': row['email'],
                'location': row['location'],
                'school': row['school'],
                'education': row['education'],
                'age': row['age'],
                'gender': row['gender'],
                'skills': skills,
                'add' : row['additional'],
                'likes': row['likes'],
                'dislikes' : row['dislikes']
            }
            doctors.append(doctor)


        return render_template('doctors.html', doctors=doctors, search=search_un)
    else:
        # Filler for now
        doctors =[]

        with sqlite3.connect('app.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT name, email, location, school, education, age, gender, skills, additional, likes, dislikes FROM users WHERE type=(?)", ("doctor",))
            rows = cur.fetchall()

        for row in rows:
            skills_un = row['skills']
            # Parse
            skills = skills_un.split(",")
            doctor = {
                'name': row['name'],
                'email': row['email'],
                'location': row['location'],
                'school': row['school'],
                'education': row['education'],
                'age': row['age'],
                'gender': row['gender'],
                'skills': skills,
                'add' : row['additional'],
                'likes': row['likes'],
                'dislikes' : row['dislikes']
            }
            doctors.append(doctor)

        return render_template('doctors.html', doctors=doctors)

@app.route('/patients', methods=['GET', 'POST'])
def patients():
    if request.method == 'POST':
        search = request.form['search']
        # Get the patients from the db where criteria meets search
        patients =[{
        'name': 'John',
        'email': 'john@email.com',
        'location': 'tokyo',
        'age': '25',
        'gender': 'male',
        'diseases': {'common flu': '90', 'cancer': '30'},
        'add' : 'whatever they wanna add'
        }]

        return render_template('patients.html', patients=patients, search=search)
    else:
        patients =[]

        # Get patient details from db
        with sqlite3.connect('app.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT name, email, location, age, gender, diseases, additional FROM users WHERE type=(?)", ("patient",))
            rows = cur.fetchall()

        for row in rows:
            diseases = row['diseases']
            if diseases != None:
                diseases = json.loads(diseases)
            else:
                diseases = {'Test not taken yet': '100'}

            patient ={
                'name': row['name'],
                'email': row['email'],
                'location': row['location'],
                'age': row['age'],
                'gender': row['gender'],
                'diseases': diseases,
                'add': row['additional']
            }

            patients.append(patient)

        return render_template('patients.html', patients=patients)


@app.route('/logout')
def logout():
    # Remove cookies
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()