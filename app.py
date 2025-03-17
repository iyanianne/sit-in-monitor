from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3  
import os
from werkzeug.utils import secure_filename
import dbhelper

app = Flask(__name__)
app.secret_key = "database1234!"
app.config['UPLOAD_FOLDER'] = 'static/images/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        idno = request.form["idno"]
        lastname = request.form["lastname"]
        fname = request.form["fname"]
        mname = request.form["mname"]
        course = request.form["course"]
        yrlvl = request.form["yrlvl"]
        email = request.form["email"]
        username = request.form["username"] if request.form['username'] else idno
        password = request.form["password"]

        try:
            # Call the function from dbhelper to add user
            dbhelper.add_user(idno, lastname, fname, mname, course, yrlvl, email, username, password)
            flash('Registration Successful! You can now log in.', 'success')
        except sqlite3.IntegrityError:
            flash('IDNO or Username already exists!', 'danger')

        return render_template("login.html")

# Login route
@app.route('/')
def index():
    return render_template('login.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["idno, username"]
        password = request.form["password"]

        # fetch user info from dbhelper
        user = dbhelper.get_user_by_username_and_password(username, password)
        admin = dbhelper.get_admin_by_username_and_password(username, password)
            
        if user:
            # Store user info in session
            session['idno'] = user[0]  # IDNO
            session['fname'] = user[1]  # First name
            session['lastname'] = user[2]  # Last name
            session['mname'] = user[3]  # Middle name
            session['course'] = user[4]  # Course
            session['yrlvl'] = user[5]  # Year level
            session['email'] = user[6]  # Email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        elif admin: 
            # Store user info in session
            session['username'] = admin[0]  # admin username
            flash('Admin Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        else:
            flash('Invalid username or password!', 'danger')
            return redirect(url_for('index'))

    return render_template("login.html")

# Dashboard route
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if "idno" in session:  # Check for the correct session key
        #  fetch user info from dbhelper
        user = dbhelper.get_user_by_id(session["idno"])
        
        if user:
            username = {
                "idno": user[0],
                "fname": user[1],
                "lastname": user[2],
                "mname": user[3],
                "course": user[4],
                "yrlvl": user[5],
                "email": user[6],
                "avatar_filename": user[7]  # Add avatar filename
            }
            return render_template("dashboard.html", username=username)
    else:
        flash("Please log in to continue.", "info")
        return redirect(url_for('index'))
    
# Information Route
@app.route('/information', methods=['GET'])
def information():
    if "idno" in session:  # Check for the correct session key
        # Retrieve user information from the database
        user = dbhelper.get_user_by_id(session["idno"])
        
        if user:
            username = {
                "idno": user[0],
                "fname": user[1],
                "lastname": user[2],
                "mname": user[3],
                "course": user[4],
                "yrlvl": user[5],
                "email": user[6],
                "avatar_filename": user[7]  # Add avatar filename to the dictionary
            }
            return render_template("information.html", username=username)
        else:
            flash("User  not found.", "danger")
            return redirect(url_for('index'))
    else:
        flash("Please log in to continue.", "info")
        return redirect(url_for('index'))
    
#Edit Student
@app.route("/edit", methods=["GET", "POST"])
def edit():
    if "idno" in session:  # Check for the correct session key
        idno = session["idno"]  # Use the IDNO for display
        student = dbhelper.get_user_by_id(idno)
        
        if request.method == "POST":
            avatar = request.files.get('avatar')
            if avatar:
                avatar_filename = secure_filename(avatar.filename)
                avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename))
                # Update the avatar filename in the database
                dbhelper.update_user_avatar(idno, avatar_filename)

            # Handle other user details
            lastname = request.form.get('lastname')
            fname = request.form.get('fname')
            mname = request.form.get('mname')
            course = request.form.get('course')
            yrlvl = request.form.get('yrlvl')
            email = request.form.get('email')

            # Update the user details in the database
            dbhelper.update_user(idno, lastname, fname, mname, course, yrlvl, email)
            
            flash("User  details updated successfully.", "success")
            return redirect(url_for('dashboard'))  # Redirect to the dashboard or another page
        
        if student:
            return render_template('edit.html', student=student)
        else:
            flash("User  not found.", "danger")
            return redirect(url_for('dashboard'))
    else: 
        flash('Please log in to continue.', "info")    
        return redirect(url_for('login'))  # Redirect to login page instead of rendering edit.html  # Redirect to login page instead of rendering edit.html

# Lab Rules route
@app.route('/labrules')
def labrules():
    return render_template('labrules.html')
    
# Sit-in Rules route
@app.route('/sit-in')
def sit_in():
    return render_template('sit-in.html')
    

# ADMIN ROUTES
# Admin Dashboard route
@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if "username" not in session:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))

    if request.method == 'POST':
        password = request.form.get('password')
        if password:
            admin = dbhelper.get_admin_by_username_and_password(session['username'], password)
            if admin:
                username = {"username": admin[0]}
                return render_template("admin_dashboard.html", username=username)
            else:
                flash("Invalid admin credentials.", "danger")
                return redirect(url_for("index"))
        else:
            flash("Password is required.", "danger")
            return redirect(url_for("admin_dashboard"))

    return render_template("admin_dashboard.html")  # Handle the GET request

# Logout route
@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("idno", None)  # Use the correct session key
    session.pop("fname", None)  # Clear the first name as well
    flash("Successfully logged out!", "info")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)