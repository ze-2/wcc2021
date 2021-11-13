from flask import Flask, redirect, request, render_template, url_for

app = Flask(__name__, static_url_path='/static')

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
        if type == "doctor":
            return redirect(url_for('doctor'))
        else:
            return redirect(url_for('patient'))

    else:
        return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Signup details from user? Need to add more criteria
        username = request.form['username']
        password = request.form['password']
        # Doctor or patient
        user_type = request.form['user_type']
        # Check with the db if account exists, if not create account
        return redirect(url_for('home'))
    else:
        return render_template('signup.html')


# Home page after patient logs in
# Patient can take the test, view the available doctors or their results from the last time
@app.route('/user', methods=['GET', 'POST'])
def user():
    # db works
    return render_template('user.html')

# Home page after doctor logs in
# Here they can see patients and their details, likely diseases etc.
@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
    return render_template('doctor.html')

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
# Eg. doctors = [{'name': 'Dr. Smith', 'address': '123 Main St.', 'phone': '555-555-5555'}, {'name': 'Dr. Jones', 'address': '456 Main St.', 'phone': '555-555-5555'}]
@app.route('/doctors', methods=['GET', 'POST'])
def doctors():
    # Need to get doctors from db here
    return render_template('doctors.html')

if __name__ == "__main__":
    app.run()