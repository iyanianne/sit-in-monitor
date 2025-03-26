from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import sqlite3  
import os
from werkzeug.utils import secure_filename
import dbhelper
from datetime import datetime

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
<<<<<<< HEAD
            # Store user info in session
            session['idno'] = user[0]  # IDNO
            session['lastname'] = user[1]  # Last name
            session['fname'] = user[2]  # First name
            session['mname'] = user[3]  # Middle name
            session['course'] = user[4]  # Course
            session['yrlvl'] = user[5]  # Year level
            session['email'] = user[6]  # Email
            session['username'] = user[8]  # Username
            session['remaining_sessions'] = user[10]  # Remaining sessions
            session['total_sessions'] = user[11]  # Total sessions
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
=======
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
>>>>>>> c3146be3e2a7c5b4ea2af77a924be396b12ef12b
        
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
<<<<<<< HEAD
    if "idno" in session:  # Check for the correct session key
        # Create user dictionary from session data
        user = {
            "idno": session["idno"],
            "fname": session["fname"],
            "lastname": session["lastname"],
            "mname": session["mname"],
            "course": session["course"],
            "yrlvl": session["yrlvl"],
            "email": session["email"],
            "remaining_sessions": session.get("remaining_sessions", 30),
            "total_sessions": session.get("total_sessions", 30)
        }
        # Get announcements from session
        announcements = session.get('announcements', [])
        return render_template("dashboard.html", username=user, announcements=announcements)
    else:
        flash("Please log in to continue.", "info")
=======
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
>>>>>>> c3146be3e2a7c5b4ea2af77a924be396b12ef12b
        return redirect(url_for('login'))
    
# Information Route
@app.route('/information', methods=['GET'])
def information():
    if "idno" in session:
        # Get user data including avatar from database
        user_data = dbhelper.get_user_by_id(session["idno"])
        
<<<<<<< HEAD
        # Create user dictionary from database data
        user = {
            "idno": session["idno"],
            "fname": session["fname"],
            "lastname": session["lastname"],
            "mname": session["mname"],
            "course": session["course"],
            "yrlvl": session["yrlvl"],
            "email": session["email"],
            "avatar_filename": user_data[7] if user_data and len(user_data) > 7 else None,  # Get avatar filename from database
            "remaining_sessions": session.get("remaining_sessions", 30),
            "total_sessions": session.get("total_sessions", 30)
        }
        return render_template("information.html", username=user)
=======
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
>>>>>>> c3146be3e2a7c5b4ea2af77a924be396b12ef12b
    else:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))
    
#Edit Student
@app.route("/edit", methods=["GET", "POST"])
def edit():
    if "idno" not in session:  # Check if user is not logged in
        flash('Please log in to continue.', "info")    
        return redirect(url_for('login'))

    idno = session["idno"]  # Use the IDNO for display
    student = dbhelper.get_user_by_id(idno)
    
    # Create user dictionary from session data
    user = {
        "idno": session["idno"],
        "fname": session["fname"],
        "lastname": session["lastname"],
        "mname": session["mname"],
        "course": session["course"],
        "yrlvl": session["yrlvl"],
        "email": session["email"],
        "remaining_sessions": session.get("remaining_sessions", 30),
        "total_sessions": session.get("total_sessions", 30)
    }
    
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
        
        # Update session data with new values
        session['lastname'] = lastname
        session['fname'] = fname
        session['mname'] = mname
        session['course'] = course
        session['yrlvl'] = yrlvl
        session['email'] = email
        
        flash("User details updated successfully.", "success")
        return redirect(url_for('dashboard'))
    
    # For GET requests, display the edit form
    if student:
        # Convert student tuple to list format for template compatibility
        student_list = list(student)  # The order is already correct from the database query
        return render_template('edit.html', student=student_list, username=user)
    else:
        flash("User not found.", "danger")
        return redirect(url_for('dashboard'))

# Announcement route
@app.route('/announcement')
def announcement():
    if "idno" in session:
        # Create user dictionary from session data
        user = {
            "idno": session["idno"],
            "fname": session["fname"],
            "lastname": session["lastname"],
            "mname": session["mname"],
            "course": session["course"],
            "yrlvl": session["yrlvl"],
            "email": session["email"],
            "remaining_sessions": session.get("remaining_sessions", 30),
            "total_sessions": session.get("total_sessions", 30)
        }
        # Get announcements from session
        announcements = session.get('announcements', [])
        return render_template('announcement.html', username=user, announcements=announcements)
    else:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))

# Lab Rules route
@app.route('/labrules')
def labrules():
    if "idno" in session:
        # Create user dictionary from session data
        user = {
            "idno": session["idno"],
            "fname": session["fname"],
            "lastname": session["lastname"],
            "mname": session["mname"],
            "course": session["course"],
            "yrlvl": session["yrlvl"],
            "email": session["email"],
            "remaining_sessions": session.get("remaining_sessions", 30),
            "total_sessions": session.get("total_sessions", 30)
        }
        return render_template('labrules.html', username=user)
    else:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))
    
# Sit-in Rules route
@app.route('/sit-in')
def sit_in():
    if "idno" in session:
        # Create user dictionary from session data
        user = {
            "idno": session["idno"],
            "fname": session["fname"],
            "lastname": session["lastname"],
            "mname": session["mname"],
            "course": session["course"],
            "yrlvl": session["yrlvl"],
            "email": session["email"],
            "remaining_sessions": session.get("remaining_sessions", 30),
            "total_sessions": session.get("total_sessions", 30)
        }
        return render_template('sit-in.html', username=user)
    else:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))
    

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
    currently_sit_in = dbhelper.count_currently_sit_in()  # Get current day's sit-in count
    total_sit_in = dbhelper.count_total_sit_in()
    
    # Get sit-in purposes data
    purposes_data = dbhelper.get_sit_in_purposes_distribution()
    purposes_labels = [purpose[0] for purpose in purposes_data]
    purposes_counts = [purpose[1] for purpose in purposes_data]
    
    # Get announcements from session
    announcements = session.get('announcements', [])
    
    return render_template("admin_dashboard.html", 
                         announcements=announcements,
                         students_registered=students_registered,
                         currently_sit_in=currently_sit_in,
                         total_sit_in=total_sit_in,
                         purposes_labels=purposes_labels,
                         purposes_data=purposes_counts)

# Announcement route
@app.route('/add_announcement', methods=['POST'])
def add_announcement():
    if "username" not in session:
        return redirect(url_for('login'))
    
    title = request.form.get('title')
    content = request.form.get('content')
    
    if title and content:
        # Initialize announcements list in session if it doesn't exist
        if 'announcements' not in session:
            session['announcements'] = []
        
        # Add new announcement to the list
        session['announcements'].append({
            "title": title,
            "content": content,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        
        # Keep only the last 10 announcements
        if len(session['announcements']) > 10:
            session['announcements'] = session['announcements'][-10:]
        
        flash('Announcement posted successfully!', 'success')
    else:
        flash('Title and content are required!', 'danger')

    return redirect(url_for('admin_dashboard'))

# Admin Students List Route
selected_data = {}

# Students List Route
@app.route('/ad_students')
def ad_students():
    if "username" not in session:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))

    students = dbhelper.get_all_students()
    return render_template('ad_students.html', students=students)

# Reports route
@app.route('/ad_reports')
def ad_reports():
    if "username" not in session:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))

    reports = dbhelper.get_sit_in_reports()
    return render_template('ad_reports.html', reports=reports)

# Records route
@app.route('/ad_records')
def ad_records():
    if "username" not in session:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))

    records = dbhelper.get_sit_in_records()
    return render_template('ad_records.html', records=records)

# Sit-In route
@app.route('/ad_sit-in')
def ad_sit_in():
    if "username" not in session:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))

    # Get all currently sitting in students
    current_students = dbhelper.get_current_sit_in_students()
    return render_template('ad_sit-in.html', students=current_students)

# End Sit-In route
@app.route('/end_sit_in/<int:idno>', methods=['POST'])
def end_sit_in(idno):
    if "username" not in session:
        return jsonify({"error": "Not authorized"}), 401

    try:
        # Update the sit-in record with end time
        dbhelper.end_sit_in_session(idno)
        # Decrement the remaining sessions
        dbhelper.decrement_student_session(idno)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Sit-In form route
@app.route('/sitinform/<int:idno>', methods=['GET'])
def sitinform(idno):
    try:
        # Convert to string for database query
        idno_str = str(idno)
        student = dbhelper.get_user_by_id(idno_str)

        if student:
            # Make sure we have all the needed data
            remaining_sessions = student[8] if len(student) > 8 else 30
            total_sessions = student[9] if len(student) > 9 else 30
            
            student_data = {
                "idno": student[0],
                "lastname": student[1],
                "fname": student[2],
                "mname": student[3] if student[3] else "",
                "course": student[4],
                "yrlvl": student[5],
                "email": student[6],
                "name": f"{student[2]} {student[3] if student[3] else ''} {student[1]}",  # Format: fname mname lastname
                "remaining_sessions": remaining_sessions,
                "total_sessions": total_sessions
            }
            return jsonify(student_data)
        return jsonify({"error": "Student not found."}), 404
    except Exception as e:
        print(f"Error in sitinform: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error retrieving student information."}), 500
    
# Logout route
@app.route("/logout")
def logout():
    # Clear all session data
    session.clear()
    flash("Successfully logged out!", "info")
    return redirect(url_for('index'))

<<<<<<< HEAD
# Sessions route
@app.route('/sessions')
def sessions():
    if 'idno' not in session:
        flash('Please log in to view your sessions.')
        return redirect(url_for('login'))
    
    idno = session['idno']
    user = {
        'idno': session['idno'],
        'fname': session['fname'],
        'lastname': session['lastname'],
        'mname': session['mname'],
        'course': session['course'],
        'yrlvl': session['yrlvl'],
        'email': session['email'],
        'avatar_filename': session.get('avatar_filename', 'default.png'),
        'remaining_sessions': session.get('remaining_sessions', 30),
        'total_sessions': session.get('total_sessions', 30)
    }
    
    # Get the remaining and total sessions directly from the session
    remaining_sessions = session.get('remaining_sessions', 30)
    total_sessions = session.get('total_sessions', 30)
    percentage = (remaining_sessions / total_sessions) * 100 if total_sessions > 0 else 0
    
    # Create sessions data for the template
    sessions_data = {
        'remaining': remaining_sessions,
        'total': total_sessions,
        'percentage': percentage
    }
    
    return render_template('sessions.html', 
                         username=user,
                         sessions=sessions_data)

# History route
@app.route('/history')
def history():
    if 'idno' not in session:
        flash('Please log in to view your history.')
        return redirect(url_for('login'))
    
    idno = session['idno']
    user = {
        'idno': session['idno'],
        'fname': session['fname'],
        'lastname': session['lastname'],
        'mname': session['mname'],
        'course': session['course'],
        'yrlvl': session['yrlvl'],
        'email': session['email'],
        'avatar_filename': session.get('avatar_filename', 'default.png'),
        'remaining_sessions': session.get('remaining_sessions', 30),
        'total_sessions': session.get('total_sessions', 30)
    }
    
    # Get history information
    history = dbhelper.get_student_history(idno)
    
    return render_template('history.html', username=user, history=history)

# Sit-In route
@app.route('/process_sit_in', methods=['POST'])
def process_sit_in():
    if "username" not in session:
        return jsonify({"error": "Not authorized"}), 401

    try:
        data = request.get_json()
        idno = data.get('idno')
        purpose = data.get('purpose')
        laboratory = data.get('laboratory')

        print(f"Received sit-in request: idno={idno}, purpose={purpose}, laboratory={laboratory}")

        if not all([idno, purpose, laboratory]):
            return jsonify({"error": "Missing required fields"}), 400

        idno = str(idno).strip()

        dbhelper.initialize_student_sessions(idno)
        
        student_info = dbhelper.get_student_sessions(idno)
        if not student_info or (student_info and student_info[1] <= 0):
            return jsonify({"error": "Student has no remaining sessions"}), 400
        
        dbhelper.update_sit_in_status(idno, purpose, laboratory)
        
        dbhelper.decrement_student_session(idno)
        
        if 'idno' in session and session['idno'] == idno:
            # Get current values
            student_info = dbhelper.get_student_sessions(idno)
            if student_info:
                _, remaining_sessions, total_sessions = student_info
                session['remaining_sessions'] = remaining_sessions
                session['total_sessions'] = total_sessions
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error in process_sit_in: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Feedbacks route
@app.route('/feedback')
def feedback():
    if "username" not in session:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))
    
    return render_template('feedback.html')
=======
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
>>>>>>> c3146be3e2a7c5b4ea2af77a924be396b12ef12b

if __name__ == "__main__":
    app.run(debug=True)