from flask import Flask, flash, redirect, request, render_template, url_for, session
from flask_sslify import SSLify
import secrets

from markupsafe import re

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
        # Check with the db here
        # Get the user's type (doctor or patient here) and redirect to the appropriate page

        # Filler for now
        type = "doctor"

        # Check if details match
        check = True

        if check:
            if type == "doctor":
                # Pull from db if the user has confirmed details

                # Set the cookie to False if they haven't took the quiz
                session['details'] = False

                # Set cookies, log in as doctor
                session['username'] = username
                session['type'] = "doctor"

                flash('You are now logged in as a doctor.', 'alert alert-dismissible alert-success')
                return redirect(url_for('doctor'))
            else:
                # Pull from db if the user has confirmed details

                # Set the cookie to False if they haven't took the quiz
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
        exists = False
        if (exists):
            flash('Account already exists, choose a different username.', 'alert alert-dismissible alert-danger')
            return redirect(url_for('signup'))
        else:
            # Create account with db here
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
                return render_template('user.html', username=username)
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
                return render_template('doctor.html', username=username)
            else:
                # They haven't filled in the quiz
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
        # Update db where username = ...
        if session.get('type') == "doctor":
            username = session.get('username')

            name = request.form['name']
            location = request.form['location']
            school = request.form['school']
            age = request.form['age']
            gender = request.form['gender']
            add = request.form['add']

            skills_unparsed = request.form['skills']
            # Parse array for db - not very sure if this works, but it should be an array now
            skills = skills_unparsed.split(",")

            # For this I'll need you to store the results in full form - parse it
            # Refer to doctor_quiz page for the values and what they correspond with
            education = request.form['education']

            # Update db to say that they've filled in the quiz
            session['details'] = True

            flash('Thank you!', 'alert alert-dismissible alert-success')
            return redirect(url_for('doctor'))
        else:
            username = session.get('username')
            name = request.form['name']
            location = request.form['location']
            age = request.form['age']
            gender = request.form['gender']

            # Update db to say that they've filled in the quiz
            session['details'] = True

            flash('Thank you!', 'alert alert-dismissible alert-success')
            return redirect(url_for('user'))


    else:
        if session.get('type') == "doctor":
            return render_template('doctor_quiz.html')
        else:
            return render_template('patient_quiz.html')

# Chatbot / quiz things
# Pass final results in a list of dicts
# Eg. diseases = [{'disease': 'flu', 'score': '100'}, {'disease': 'cancer', 'score': '50'}]
@app.route('/evaluate', methods =["GET", "POST"])
def evaluate():
    if request.method == "POST":
        # Add their likely dieases to the db
        return render_template('results.html')
    else:
        return render_template('evaluate.html')

# Contains the doctors so the users can see who is available
# Pass results in a list of dicts
""" Eg.
doctors =[
{
    'name': 'Dr. Smith',
    'email': 'smith@email.com',
    'location': 'tokyo',
    'school': 'school A',
    'education': "Master's" OR "Doctorate's / Higher" OR "Bachelor's" OR "High School" OR "Vocational"
    'age': '25',
    'gender': 'male', OR 'female' OR 'others'
    'skills': ['neurologist'],
    'likes': '4',
    'dislikes' : '0'
},{
    (second and other entries in the format above)
}
]"""


@app.route('/doctors', methods=['GET', 'POST'])
def doctors():
    if request.method == 'POST':
        search = request.form['search']
        # Get the doctors from the db where criteria meets search
        # Filler
        doctors =[{
        'name': 'Dr. Smith',
        'email': 'smith@email.com',
        'location': 'Tokyo',
        'school': 'school A',
        'education': "Master's",
        'age': '25',
        'gender': 'male',
        'skills': ['neurologist'],
            'add' : 'additional info they handed up',

        'likes': '4',
        'dislikes' : '0'}]

        return render_template('doctors.html', doctors=doctors, search=search)
    else:
        # Filler for now
        doctors =[{
        'name': 'Dr. Smith',
        'email': 'smith@email.com',
        'location': 'Tokyo',
        'school': 'school A',
        'education': "Master's",
        'age': '25',
        'gender': 'male',
        'skills': ['neurologist'],
            'add' : 'additional info they handed up',

        'likes': '4',
        'dislikes' : '0'
    },{
        'name': 'Dr. Jones',
        'email': 'jones@email.com',
        'location': 'Malaysia',
        'school': 'schoolB',
        'education': "Doctorate's",
        'age': '25',
        'gender': 'others',
        'skills': ['general practitioner', 'allergist'],
        'likes': '1000',
        'dislikes' : '20'
    },{
        'name': 'Dr. Jane',
        'email': 'jane@email.com',
        'location': 'Singapore',
        'school': 'school C',
        'education': "Bachelor's",
        'age': '25',
        'gender': 'female',
        'skills': ['general practitioner', 'nutrition', 'cancer'],
        'likes': '90',
        'add' : 'whatever they wanna add',
        'dislikes' : '1'
    }]
        return render_template('doctors.html', doctors=doctors)

@app.route('/patients', methods=['GET', 'POST'])
def patients():
    # Filler for now
    patients = [{
    'name': 'John',
    'email': 'john@email.com',
    'location': 'tokyo',
    'age': '25',
    'gender': 'male',
    'diseases': [{'common flu': '90', 'cancer': '30'}]
},{
    'name': 'Jane',
    'email': 'doe@email.com',
    'location': 'malaysia',
    'age': '70',
    'gender': 'female',
    'diseases': [{'stroke': '90', 'diabetes (type 2)': '30'}]
}]
    # Need to get patients from db here in the format above
    return render_template('patients.html', patients=patients)


@app.route('/logout')
def logout():
    # Remove cookies
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()