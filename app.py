from flask import Flask, flash, redirect, request, render_template, url_for, session
from flask_sslify import SSLify
import secrets
import sqlite3
import json
from prediction import predict

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
        with sqlite3.connect('/app.db') as con:
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
                with sqlite3.connect('/app.db') as con:
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
                with sqlite3.connect('/app.db') as con:
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
        else:
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
        with sqlite3.connect('/app.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT type FROM users WHERE username = (?)", (username,))
            rows = cur.fetchall()

        if len(rows) != 0:
            flash('Account already exists, choose a different username.', 'alert alert-dismissible alert-danger')
            return redirect(url_for('signup'))

        # Create account with db here

        with sqlite3.connect('/app.db') as con:
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
                with sqlite3.connect('/app.db') as con:
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

                with sqlite3.connect('/app.db') as con:
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute("SELECT name, email, location, school, education, age, gender, skills, additional, likes, dislikes, diseases FROM users WHERE username = (?)", (username,))
                    rows = cur.fetchall()

                rows = rows[0]

                diseases = rows['diseases']
                if diseases != None:
                    diseases = json.loads(diseases)
                else:
                    diseases = {'Test not taken yet': '100'}

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
                    'dislikes' : rows['dislikes'],
                    'diseases' : diseases
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

            with sqlite3.connect('/app.db') as con:
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

            with sqlite3.connect('/app.db') as con:
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
        # Call AI function here
        itching = request.form['itching']
        skin_rash = request.form['skin_rash']
        nodal_skin_eruptions = request.form['nodal_skin_eruptions']
        continuous_sneezing = request.form['continuous_sneezing']
        shivering = request.form['shivering']
        chills = request.form['chills']
        joint_pain = request.form['joint_pain']
        stomach_pain = request.form['stomach_pain']
        acidity = request.form['acidity']
        ulcers_on_tongue = request.form['ulcers_on_tongue']
        muscle_wasting = request.form['muscle_wasting']
        vomiting = request.form['vomiting']
        burning_micturition = request.form['burning_micturition']
        spotting_urination = request.form['spotting_urination']
        fatigue = request.form['fatigue']
        weight_gain = request.form['weight_gain']
        anxiety = request.form['anxiety']
        cold_hands_and_feets = request.form['cold_hands_and_feets']
        mood_swings = request.form['mood_swings']
        weight_loss = request.form['weight_loss']
        restlessness = request.form['restlessness']
        lethargy = request.form['lethargy']
        patches_in_throat = request.form['patches_in_throat']
        irregular_sugar_level = request.form['irregular_sugar_level']
        cough = request.form['cough']
        high_fever = request.form['high_fever']
        sunken_eyes = request.form['sunken_eyes']
        breathlessness = request.form['breathlessness']
        sweating = request.form['sweating']
        dehydration = request.form['dehydration']
        indigestion = request.form['indigestion']
        headache = request.form['headache']
        yellowish_skin = request.form['yellowish_skin']
        dark_urine = request.form['dark_urine']
        nausea = request.form['nausea']
        loss_of_appetite = request.form['loss_of_appetite']
        pain_behind_the_eyes = request.form['pain_behind_the_eyes']
        back_pain = request.form['back_pain']
        constipation = request.form['constipation']
        abdominal_pain = request.form['abdominal_pain']
        diarrhoea = request.form['diarrhoea']
        mild_fever = request.form['mild_fever']
        yellow_urine = request.form['yellow_urine']
        yellowing_of_eyes = request.form['yellowing_of_eyes']
        acute_liver_failure = request.form['acute_liver_failure']
        fluid_overload = request.form['fluid_overload']
        swelling_of_stomach = request.form['swelling_of_stomach']
        swelled_lymph_nodes = request.form['swelled_lymph_nodes']
        malaise = request.form['malaise']
        blurred_and_distorted_vision = request.form['blurred_and_distorted_vision']
        phlegm = request.form['phlegm']
        throat_irritation = request.form['throat_irritation']
        redness_of_eyes = request.form['redness_of_eyes']
        sinus_pressure = request.form['sinus_pressure']
        runny_nose = request.form['runny_nose']
        congestion = request.form['congestion']
        chest_pain = request.form['chest_pain']
        weakness_in_limbs = request.form['weakness_in_limbs']
        fast_heart_rate = request.form['fast_heart_rate']
        pain_during_bowel_movements = request.form['pain_during_bowel_movements']
        pain_in_anal_region = request.form['pain_in_anal_region']
        bloody_stool = request.form['bloody_stool']
        irritation_in_anus = request.form['irritation_in_anus']
        neck_pain = request.form['neck_pain']
        dizziness = request.form['dizziness']
        cramps = request.form['cramps']
        bruising = request.form['bruising']
        obesity = request.form['obesity']
        swollen_legs = request.form['swollen_legs']
        swollen_blood_vessels = request.form['swollen_blood_vessels']
        puffy_face_and_eyes = request.form['puffy_face_and_eyes']
        enlarged_thyroid = request.form['enlarged_thyroid']
        brittle_nails = request.form['brittle_nails']
        swollen_extremeties = request.form['swollen_extremeties']
        excessive_hunger = request.form['excessive_hunger']
        extra_marital_contacts = request.form['extra_marital_contacts']
        drying_and_tingling_lips = request.form['drying_and_tingling_lips']
        slurred_speech = request.form['slurred_speech']
        knee_pain = request.form['knee_pain']
        hip_joint_pain = request.form['hip_joint_pain']
        muscle_weakness = request.form['muscle_weakness']
        stiff_neck = request.form['stiff_neck']
        swelling_joints = request.form['swelling_joints']
        movement_stiffness = request.form['movement_stiffness']
        spinning_movements = request.form['spinning_movements']
        loss_of_balance = request.form['loss_of_balance']
        unsteadiness = request.form['unsteadiness']
        weakness_of_one_body_side = request.form['weakness_of_one_body_side']
        loss_of_smell = request.form['loss_of_smell']
        bladder_discomfort = request.form['bladder_discomfort']
        foul_smell_of_urine = request.form['foul_smell_of_urine']
        continuous_feel_of_urine = request.form['continuous_feel_of_urine']
        passage_of_gases = request.form['passage_of_gases']
        internal_itching = request.form['internal_itching']
        toxic_look = request.form['toxic_look']
        depression = request.form['depression']
        irritability = request.form['irritability']
        muscle_pain = request.form['muscle_pain']
        altered_sensorium = request.form['altered_sensorium']
        red_spots_over_body = request.form['red_spots_over_body']
        belly_pain = request.form['belly_pain']
        abnormal_menstruation = request.form['abnormal_menstruation']
        dischromic_patches = request.form['dischromic_patches']
        watering_from_eyes = request.form['watering_from_eyes']
        increased_appetite = request.form['increased_appetite']
        polyuria = request.form['polyuria']
        family_history = request.form['family_history']
        mucoid_sputum = request.form['mucoid_sputum']
        rusty_sputum = request.form['rusty_sputum']
        lack_of_concentration = request.form['lack_of_concentration']
        visual_disturbances = request.form['visual_disturbances']
        receiving_blood_transfusion = request.form['receiving_blood_transfusion']
        receiving_unsterile_injections = request.form['receiving_unsterile_injections']
        coma = request.form['coma']
        stomach_bleeding = request.form['stomach_bleeding']
        distention_of_abdomen = request.form['distention_of_abdomen']
        history_of_alcohol_consumption = request.form['history_of_alcohol_consumption']
        blood_in_sputum = request.form['blood_in_sputum']
        prominent_veins_on_calf = request.form['prominent_veins_on_calf']
        palpitations = request.form['palpitations']
        painful_walking = request.form['painful_walking']
        pus_filled_pimples = request.form['pus_filled_pimples']
        blackheads = request.form['blackheads']
        scurring = request.form['scurring']
        skin_peeling = request.form['skin_peeling']
        silver_like_dusting = request.form['silver_like_dusting']
        small_dents_in_nails = request.form['small_dents_in_nails']
        inflammatory_nails = request.form['inflammatory_nails']
        blister = request.form['blister']
        red_sore_around_nose = request.form['red_sore_around_nose']
        yellow_crust_ooze = request.form['yellow_crust_ooze']

        diseases = predict(itching, skin_rash, nodal_skin_eruptions, continuous_sneezing, shivering, chills, joint_pain, stomach_pain, acidity, ulcers_on_tongue, muscle_wasting, vomiting, burning_micturition, spotting_urination, fatigue, weight_gain, anxiety, cold_hands_and_feets, mood_swings, weight_loss, restlessness, lethargy, patches_in_throat, irregular_sugar_level, cough, high_fever, sunken_eyes, breathlessness, sweating, dehydration, indigestion, headache, yellowish_skin, dark_urine, nausea, loss_of_appetite, pain_behind_the_eyes, back_pain, constipation, abdominal_pain, diarrhoea, mild_fever, yellow_urine, yellowing_of_eyes, acute_liver_failure, fluid_overload, swelling_of_stomach, swelled_lymph_nodes, malaise, blurred_and_distorted_vision, phlegm, throat_irritation, redness_of_eyes, sinus_pressure, runny_nose, congestion, chest_pain, weakness_in_limbs, fast_heart_rate, pain_during_bowel_movements, pain_in_anal_region, bloody_stool, irritation_in_anus, neck_pain, dizziness, cramps, bruising, obesity, swollen_legs, swollen_blood_vessels, puffy_face_and_eyes, enlarged_thyroid, brittle_nails, swollen_extremeties, excessive_hunger, extra_marital_contacts, drying_and_tingling_lips, slurred_speech, knee_pain, hip_joint_pain, muscle_weakness, stiff_neck, swelling_joints, movement_stiffness, spinning_movements, loss_of_balance, unsteadiness, weakness_of_one_body_side, loss_of_smell, bladder_discomfort, foul_smell_of_urine, continuous_feel_of_urine, passage_of_gases, internal_itching, toxic_look, depression, irritability, muscle_pain, altered_sensorium, red_spots_over_body, belly_pain, abnormal_menstruation, dischromic_patches, watering_from_eyes, increased_appetite, polyuria, family_history, mucoid_sputum, rusty_sputum, lack_of_concentration, visual_disturbances, receiving_blood_transfusion, receiving_unsterile_injections, coma, stomach_bleeding, distention_of_abdomen, history_of_alcohol_consumption, blood_in_sputum, prominent_veins_on_calf, palpitations, painful_walking, pus_filled_pimples, blackheads, scurring, skin_peeling, silver_like_dusting, small_dents_in_nails, inflammatory_nails, blister, red_sore_around_nose, yellow_crust_ooze)

        with sqlite3.connect('/app.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("UPDATE users SET diseases=(?) WHERE username=(?)", (json.dumps(diseases), username))
            con.commit()
        flash("Check out possible diseases in your profile!", 'alert alert-dismissible alert-success')
        if session.get('type') == "doctor":
            return redirect(url_for('doctor'))
        else:
            return redirect(url_for('user'))
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
        with sqlite3.connect('/app.db') as con:
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

        with sqlite3.connect('/app.db') as con:
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
        with sqlite3.connect('/app.db') as con:
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