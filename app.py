from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import sqlite3  
import os
from werkzeug.utils import secure_filename
import dbhelper

app = Flask(__name__)
app.secret_key = "database1234!"
app.config['UPLOAD_FOLDER'] = 'static/images/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialize global variables
announcements_list = []  # Initialize this to an empty list

# Define a function to check if user is logged in
def is_user_logged_in():
    return "idno" in session

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
        username = request.form.get("username")  # Get username from form
        password = request.form.get("password")

        print(f"Login attempt - Username: {username}")  # Debug log

        # fetch user info from dbhelper
        user = dbhelper.get_user_by_idno_or_username_and_password(username, username, password)  # Pass username for both idno and username fields
        admin = dbhelper.get_admin_by_username_and_password(username, password)
            
        if user:
            print(f"User found - Raw data: {user}")  # Debug log
            
            # Print column positions for debugging
            print("COLUMN POSITIONS:")
            for i, value in enumerate(user):
                print(f"Index {i}: {value}")
            
            # Store user info in session - with proper debugging
            session.clear()  # Clear any existing session
            
            # Database schema:
            # 0:id, 1:idno, 2:lastname, 3:fname, 4:mname, 5:course, 6:yrlvl, 7:email, 8:username, 9:password, etc.
            try:
                # Set session values properly according to the schema
                session['id'] = user[0]
                session['idno'] = user[1]
                session['lastname'] = user[2]
                session['fname'] = user[3]
                session['mname'] = user[4]
                session['course'] = user[5]
                session['yrlvl'] = user[6]
                session['email'] = user[7]
                session['username'] = user[8]
                
                # Avatar filename is at index 11
                if len(user) > 11:
                    session['avatar_filename'] = user[11]
                
                session.modified = True  # Ensure session is saved
                print(f"Session after login: {dict(session)}")  # Debug log
                
                # Try debugging the redirect
                print(f"Redirecting to: /dashboard")
                flash('Login successful!', 'success')
                
                # Use regular redirect
                return redirect('/dashboard')
            except Exception as e:
                print(f"Error setting session: {str(e)}")
                flash(f"Login error: {str(e)}", "danger")
                return redirect('/')
        
        elif admin: 
            print(f"Admin found: {admin}")  # Debug log
            # Store user info in session
            session.clear()  # Clear any existing session
            session['username'] = admin[0]  # admin username
            session.modified = True  # Ensure session is saved
            flash('Admin Login successful!', 'success')
            return redirect('/admin_dashboard')
        
        else:
            print("No user or admin found")  # Debug log
            flash('Invalid username or password!', 'danger')
            return redirect('/')

    return render_template("login.html")

# Dashboard route
@app.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        print(f"Dashboard route - Raw session data: {dict(session)}")  # Debug log
        if "idno" in session:  # Check for the correct session key
            try:
                # Print each individual session value for debugging
                print(f"SESSION VALUES:")
                print(f"ID: {session.get('id')}")
                print(f"IDNO: {session.get('idno')}")
                print(f"First Name: {session.get('fname')}")
                print(f"Last Name: {session.get('lastname')}")
                print(f"Middle Name: {session.get('mname')}")
                print(f"Course: {session.get('course')}")
                print(f"Year Level: {session.get('yrlvl')}")
                print(f"Email: {session.get('email')}")
                print(f"Username: {session.get('username')}")
                print(f"Avatar: {session.get('avatar_filename')}")
                
                #  fetch user info from dbhelper
                user = dbhelper.get_user_by_id(session["idno"])  # Get user by ID
                print(f"User from database: {user}")  # Debug log
                
                if user:
                    # Create username dictionary directly from database values
                    username = {
                        "id": user["id"],
                        "idno": user["idno"],
                        "lastname": user["lastname"],
                        "fname": user["fname"],
                        "mname": user["mname"],
                        "course": user["course"],
                        "yrlvl": user["yrlvl"],
                        "email": user["email"],
                        "username": user["username"],
                        "avatar_filename": user.get("avatar_filename", None)
                    }
                    print(f"Username dict from database: {username}")  # Debug the constructed dictionary
                    return render_template("dashboard.html", username=username, announcements=announcements_list)
                else:
                    # If user is not found in database, create username dictionary from session
                    print("User not found in database but session exists")
                    username = {
                        "id": session.get("id", ""),
                        "idno": session.get("idno", ""),
                        "lastname": session.get("lastname", ""),
                        "fname": session.get("fname", ""),
                        "mname": session.get("mname", ""),
                        "course": session.get("course", ""),
                        "yrlvl": session.get("yrlvl", ""),
                        "email": session.get("email", ""),
                        "username": session.get("username", ""),
                        "avatar_filename": session.get("avatar_filename", None)
                    }
                    print(f"Username dict from session: {username}")  # Debug the constructed dictionary
                    return render_template("dashboard.html", username=username, announcements=announcements_list)
            except Exception as e:
                print(f"Error in dashboard route when getting user: {str(e)}")
                flash(f"An error occurred when retrieving user data: {str(e)}", "danger")
                # Clear the session and redirect to login
                session.clear()
                return redirect(url_for('login'))
        else:
            print("No idno in session")  # Debug log
            flash("Please log in to continue.", "info")
            return redirect(url_for('login'))
    except Exception as e:
        print(f"Unexpected error in dashboard route: {str(e)}")
        flash("An unexpected error occurred. Please try again.", "danger")
        session.clear()  # Clear session on error
        return redirect(url_for('login'))
    
    flash("Please log in to continue.", "info")  # If no session, ask to log in
    return redirect(url_for('index'))
    
# Information Route
@app.route('/information', methods=['GET'])
def information():
    if "idno" in session:  # Check for the correct session key
        # Retrieve user information from the database
        user = dbhelper.get_user_by_id(session["idno"])
        
        if user:
            username = {
                "id": user["id"],
                "idno": user["idno"],
                "lastname": user["lastname"],
                "fname": user["fname"],
                "mname": user["mname"],
                "course": user["course"],
                "yrlvl": user["yrlvl"],
                "email": user["email"],
                "username": user["username"],
                "avatar_filename": user.get("avatar_filename", None)
            }
            return render_template("information.html", username=username)
        else:
            flash("User not found.", "danger")
            return redirect(url_for('login'))
    else:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))
    
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

    students_registered = dbhelper.count_registered_students()
    currently_sit_in = session.get("currently_sit_in", 0) 
    total_sit_in = session.get("total_sit_in", 0)
    
    return render_template("admin_dashboard.html", 
                           announcements=announcements_list,
                           students_registered=students_registered,
                           currently_sit_in=currently_sit_in,
                           total_sit_in=total_sit_in)  # Handle the GET request

# Announcement route
@app.route('/add_announcement', methods=['POST'])
def add_announcement():
    if "username" not in session:
        return redirect(url_for('login'))
    
    title = request.form.get('title')
    content = request.form.get('content')
    
    if title and content:
        announcements_list.append({"title": title, "content": content})

    return redirect(url_for('ad_dashboard'))

# Admin Students List Route
selected_data = {}

@app.route('/ad_students')
def ad_students():
    if "username" not in session:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))

    student = dbhelper.get_all_students()
    if student:
        student = student [0]

    return render_template('ad_students.html', student=student)

@app.route('/sitinform/<int:idno>', methods=['GET'])
def sitinform(idno):
    student = dbhelper.get_user_by_id(idno)

    if student:
        student = {
            "idno": student[0],
            "name": student[1],
            "purpose": student[2],
            "laboratory": student[3],
            "sessions": student[4]
        }
        return jsonify(student)
    return jsonify({"error": "Student not found."}), 404
    
# Logout route
@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Successfully logged out!", "info")
    session.pop("idno", None)  # Use the correct session key
    session.pop("fname", None)  # Clear the first name as well
    flash("Successfully logged out!", "info")
    return redirect(url_for('index'))

# Debug route to check session
@app.route('/debug-session')
def debug_session():
    if "idno" in session:
        session_data = dict(session)
        idno = session.get('idno')
        
        html = "<h2>Session Data</h2>"
        html += f"<pre>{session_data}</pre>"
        
        html += "<h2>Individual Session Values</h2>"
        html += f"<p><b>ID:</b> {session.get('id')}</p>"
        html += f"<p><b>IDNO:</b> {session.get('idno')}</p>"
        html += f"<p><b>First Name:</b> {session.get('fname')}</p>"
        html += f"<p><b>Last Name:</b> {session.get('lastname')}</p>"
        html += f"<p><b>Middle Name:</b> {session.get('mname')}</p>"
        html += f"<p><b>Course:</b> {session.get('course')}</p>"
        html += f"<p><b>Year Level:</b> {session.get('yrlvl')}</p>"
        html += f"<p><b>Email:</b> {session.get('email')}</p>"
        html += f"<p><b>Username:</b> {session.get('username')}</p>"
        html += f"<p><b>Avatar Filename:</b> {session.get('avatar_filename')}</p>"
        
        html += "<h2>User Data from Database</h2>"
        user = dbhelper.get_user_by_id(idno)
        if user:
            html += f"<pre>{user}</pre>"
            
            html += "<h2>Database Fields</h2>"
            html += f"<p><b>ID:</b> {user.get('id')}</p>"
            html += f"<p><b>IDNO:</b> {user.get('idno')}</p>"
            html += f"<p><b>First Name:</b> {user.get('fname')}</p>"
            html += f"<p><b>Last Name:</b> {user.get('lastname')}</p>"
            html += f"<p><b>Middle Name:</b> {user.get('mname')}</p>"
            html += f"<p><b>Course:</b> {user.get('course')}</p>"
            html += f"<p><b>Year Level:</b> {user.get('yrlvl')}</p>"
            html += f"<p><b>Email:</b> {user.get('email')}</p>"
            html += f"<p><b>Username:</b> {user.get('username')}</p>"
            html += f"<p><b>Avatar Filename:</b> {user.get('avatar_filename')}</p>"
        else:
            html += "<p>User not found in database</p>"
            
        return html
    else:
        return "No session data found"

if __name__ == "__main__":
    app.run(debug=True)