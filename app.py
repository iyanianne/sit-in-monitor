from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify, send_file
import sqlite3  
import os
from werkzeug.utils import secure_filename
import dbhelper
from datetime import datetime, timedelta
from functools import wraps
import uuid
import shutil
import time

app = Flask(__name__)
app.secret_key = "database1234!"
app.config['UPLOAD_FOLDER'] = 'static/images/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['RESOURCE_FOLDER'] = 'static/resources'
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25 MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'zip', 'rar', 'txt'}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESOURCE_FOLDER'], exist_ok=True)

# Ensure all resource category folders exist
resource_categories = [
    'c_resources', 'java_resources', 'python_resources', 'csharp_resources',
    'database_resources', 'digilog_resources', 'iot_resources', 
    'computer_resources', 'pm_resources', 'itrends_resources',
    'techno_resources', 'capstone_resources', 'lab_manuals'
]

for category in resource_categories:
    category_path = os.path.join(app.config['RESOURCE_FOLDER'], category)
    os.makedirs(category_path, exist_ok=True)

# Initialize the database tables
def init_db():
    conn = sqlite3.connect('sitinmonitor.db')
    cursor = conn.cursor()
    
    # Create users table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idno TEXT UNIQUE NOT NULL,
        fname TEXT NOT NULL,
        lname TEXT NOT NULL,
        sectionname TEXT,
        password TEXT NOT NULL
    )
    ''')
    
    # Create sit_in table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sit_in (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idno TEXT NOT NULL,
        student_fname TEXT,
        student_lname TEXT,
        laboratory TEXT NOT NULL,
        machine_no TEXT NOT NULL,
        purpose TEXT,
        time_in TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        time_out TIMESTAMP,
        FOREIGN KEY (idno) REFERENCES users(idno)
    )
    ''')
    
    # Create resources table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        file_path TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        uploaded_by TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create settings table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_name TEXT UNIQUE NOT NULL,
        setting_value TEXT NOT NULL
    )
    ''')
    
    # Insert default settings
    try:
        cursor.execute("INSERT OR IGNORE INTO settings (setting_name, setting_value) VALUES ('resources_enabled', 'true')")
    except:
        pass
    
    conn.commit()
    conn.close()
    
    # Create resource upload directory if it doesn't exist
    os.makedirs(app.config['RESOURCE_FOLDER'], exist_ok=True)

# Initialize the database
init_db()

# Initialize database on startup
dbhelper.initialize_database()
dbhelper.ensure_lab_points_column()  # Make sure lab_points column exists
dbhelper.ensure_reservation_logs_table()  # Make sure reservation_logs table exists correctly

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'idno' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in as admin to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
        idno = request.form.get("idno")
        username = request.form.get("username")
        password = request.form.get("password")

        # fetch user info from dbhelper
        user = dbhelper.get_user_by_idno_or_username_and_password(idno, username, password)
        admin = dbhelper.get_admin_by_username_and_password(username, password)
            
        if user:
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
        return redirect(url_for('login'))
    
# Information Route
@app.route('/information', methods=['GET'])
def information():
    if "idno" in session:
        # Get user data including avatar from database
        user_data = dbhelper.get_user_by_id(session["idno"])
        
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
        "lname": session["lastname"],  # Note: Using lastname from session but lname in template
        "mname": session["mname"],
        "course": session["course"],
        "year": session["yrlvl"],  # Note: Using yrlvl from session but year in template
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
            # Update session with new avatar filename
            session['avatar_filename'] = avatar_filename

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
    return render_template("edit.html", username=user)

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
    if 'idno' not in session:
        return redirect(url_for('login'))
    
    username = dbhelper.get_user_by_id(session['idno'])
    resources_enabled = dbhelper.get_resources_enabled()
    
    return render_template('labrules.html', 
                         username=username, 
                         resources_enabled=resources_enabled)
    
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
    
    # Get statistics
    students_registered = dbhelper.count_registered_students()
    currently_sit_in = dbhelper.count_currently_sit_in()
    total_sit_in = dbhelper.count_total_sit_in()
    
    # Get purposes distribution for the chart
    purposes_data = dbhelper.get_sit_in_purposes_distribution()
    purposes_labels = [purpose[0] for purpose in purposes_data]
    purposes_counts = [purpose[1] for purpose in purposes_data]
    
    # Get leaderboard data
    leaderboard_students = dbhelper.get_sit_in_leaderboard()
    
    # Debug: print leaderboard data to console
    print("LEADERBOARD DATA:", leaderboard_students)
    
    # Get resource status
    resources_enabled = dbhelper.get_resources_enabled()
    
    # Get uploaded resources with error handling
    try:
        resources = dbhelper.get_all_resources()
    except Exception as e:
        print(f"Error retrieving resources: {e}")
        resources = []
    
    # Make sure we have access to announcements
    if 'announcements' not in session:
        session['announcements'] = []
    
    return render_template('admin_dashboard.html',
                         students_registered=students_registered,
                         currently_sit_in=currently_sit_in,
                         total_sit_in=total_sit_in,
                         purposes_labels=purposes_labels,
                         purposes_data=purposes_counts,
                         students=leaderboard_students,
                         resources_enabled=resources_enabled,
                         resources=resources,
                         announcements=session.get('announcements', []))

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
        
        # Create the new announcement with a timestamp
        new_announcement = {
            "title": title,
            "content": content,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # Add new announcement to the list
        session['announcements'].append(new_announcement)
        
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

    lab_reports = dbhelper.get_lab_reports()
    return render_template('ad_reports.html', reports=lab_reports)

# Records route
@app.route('/ad_records')
def ad_records():
    if "username" not in session:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))

    reports = dbhelper.get_sit_in_records()
    return render_template('ad_records.html', reports=reports)

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
        # Convert ID to string for database operations
        id_str = str(idno)
        
        # First check if the student has an active sit-in
        has_active_sitin = dbhelper.check_user_has_active_sitin(id_str)
        
        if not has_active_sitin:
            print(f"No active sit-in found for student {id_str}")
            return jsonify({"success": False, "message": "No active sit-in session found"}), 404
        
        # Update the sit-in record with end time
        success = dbhelper.end_sit_in_session(id_str)
        
        # Log the action
        admin_username = session.get('username', 'Unknown admin')
        if success:
            print(f"Admin {admin_username} successfully ended sit-in session for student {id_str}")
        else:
            print(f"Admin {admin_username} attempted to end sit-in session for student {id_str}, but the operation returned failure")
            return jsonify({"success": False, "message": "Failed to end sit-in session"}), 500
        
        # Add a small delay to ensure DB has updated before checking
        time.sleep(0.5)
        
        # Double-check that the session was properly ended
        still_active = dbhelper.check_user_has_active_sitin(id_str)
        if still_active:
            print(f"WARNING: Sit-in session for student {id_str} is still active after end_sit_in_session")
            return jsonify({"success": False, "message": "Failed to end sit-in session"}), 500
        
        # Success message indicates that the student can now make reservations
        return jsonify({
            "success": True, 
            "message": "Sit-in session ended successfully. Student can now make new reservations."
        })
    except Exception as e:
        print(f"Error ending sit-in session: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Sit-In form route
@app.route('/sitinform/<int:idno>', methods=['GET'])
def sitinform(idno):
    try:
        # Convert to string for database query
        idno_str = str(idno)
        student = dbhelper.get_user_by_id(idno_str)

        if student:
            # Create student data dictionary from the returned dictionary
            student_data = {
                "idno": student['idno'],
                "lastname": student['lastname'],
                "fname": student['fname'],
                "mname": student['mname'] if student['mname'] else "",
                "course": student['course'],
                "yrlvl": student['yrlvl'],
                "email": student['email'],
                "name": f"{student['fname']} {student['mname'] if student['mname'] else ''} {student['lastname']}",
                "remaining_sessions": student['remaining_sessions'],
                "total_sessions": student['total_sessions'],
                "lab_points": student['lab_points']
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

# Sessions route
@app.route('/sessions')
def sessions():
    if 'idno' not in session:
        flash('Please log in to view your sessions.')
        return redirect(url_for('login'))
    
    idno = session['idno']
    # Get the latest user data from database
    user_data = dbhelper.get_user_by_id(idno)
    sessions_data = dbhelper.get_student_sessions(idno)
    
    if not user_data:
        flash('User data not found.')
        return redirect(url_for('login'))
    
    # Get the latest remaining and total sessions
    remaining_sessions = sessions_data['remaining_sessions']
    total_sessions = sessions_data['total_sessions']
    
    # Update session with latest values
    session['remaining_sessions'] = remaining_sessions
    session['total_sessions'] = total_sessions
    
    user = {
        'idno': session['idno'],
        'fname': session['fname'],
        'lastname': session['lastname'],
        'mname': session['mname'],
        'course': session['course'],
        'yrlvl': session['yrlvl'],
        'email': session['email'],
        'avatar_filename': session.get('avatar_filename', 'default.png'),
        'remaining_sessions': remaining_sessions,
        'total_sessions': total_sessions
    }
    
    percentage = (remaining_sessions / total_sessions) * 100 if total_sessions > 0 else 0
    
    # Create sessions data for the template
    display_sessions = {
        'remaining': remaining_sessions,
        'total': total_sessions,
        'percentage': percentage
    }
    
    return render_template('sessions.html', 
                         username=user,
                         sessions=display_sessions)

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

        # Get detailed sit-in status
        sit_in_status = dbhelper.check_active_sitin_status(idno)
        
        # Check if the student already has an active sit-in session
        if sit_in_status['has_active_session']:
            print(f"Student {idno} already has an active sit-in session. Rejecting duplicate request.")
            return jsonify({"error": "Student already has an active sit-in session. Please complete the current session first."}), 400
            
        # Check if the student has any pending or approved reservations
        if dbhelper.check_user_has_pending_reservation(idno):
            print(f"Student {idno} has a pending reservation. Cannot start sit-in session.")
            return jsonify({"error": "You have a pending reservation request. Please wait for approval before starting a sit-in session."}), 400
            
        if dbhelper.check_user_has_approved_reservation(idno):
            print(f"Student {idno} has an approved reservation. Cannot start sit-in session.")
            return jsonify({"error": "You have an approved reservation. Please wait for your scheduled time."}), 400

        dbhelper.initialize_student_sessions(idno)
        
        student_info = dbhelper.get_student_sessions(idno)
        if not student_info or student_info['remaining_sessions'] <= 0:
            return jsonify({"error": "Student has no remaining sessions"}), 400
        
        dbhelper.update_sit_in_status(idno, purpose, laboratory)
        
        if 'idno' in session and session['idno'] == idno:
            # Get current values
            student_info = dbhelper.get_student_sessions(idno)
            if student_info:
                session['remaining_sessions'] = student_info['remaining_sessions']
                session['total_sessions'] = student_info['total_sessions']
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error in process_sit_in: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Feedbacks route
@app.route('/ad_feedbacks')
def ad_feedbacks():
    if "username" not in session:
        flash("Please log in to continue.", "info")
        return redirect(url_for('login'))
    
    feedbacks = dbhelper.get_all_feedbacks()
    return render_template('ad_feedbacks.html', feedbacks=feedbacks)

#  Reservations route
@app.route('/reservations')
def reservations():
    if 'idno' not in session:
        flash('Please log in to view reservations.')
        return redirect(url_for('login'))
    
    idno = session['idno']
    # Get the latest user data from database
    user_data = dbhelper.get_user_by_id(idno)
    
    if not user_data:
        flash('User data not found.')
        return redirect(url_for('login'))
    
    # Get the latest remaining and total sessions from database
    remaining_sessions = user_data[8] if user_data[8] is not None else 30
    total_sessions = user_data[9] if user_data[9] is not None else 30
    
    # Update session with latest values
    session['remaining_sessions'] = remaining_sessions
    session['total_sessions'] = total_sessions
    
    user = {
        'idno': session['idno'],
        'fname': session['fname'],
        'lastname': session['lastname'],
        'mname': session['mname'],
        'course': session['course'],
        'yrlvl': session['yrlvl'],
        'email': session['email'],
        'avatar_filename': session.get('avatar_filename', 'default.png')
    }
    
    # Create sessions data for the template
    sessions_data = {
        'remaining': remaining_sessions,
        'total': total_sessions
    }
    
    # Get user reservation history
    reservation_history = dbhelper.get_user_reservations(idno)
    
    return render_template('reservations.html', 
                         username=user,
                         sessions=sessions_data,
                         reservation_history=reservation_history)

# Reset Sessions route
@app.route('/reset_sessions/<string:idno>', methods=['POST'])
def reset_sessions(idno):
    if "username" not in session:
        return jsonify({"error": "Not authorized"}), 401
    
    try:
        # Call the function to reset student sessions
        dbhelper.reset_student_sessions(idno)
        
        # If the student is currently logged in, update their session data
        if 'idno' in session and session['idno'] == idno:
            session['remaining_sessions'] = 30
            session['total_sessions'] = 30
            
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error in reset_sessions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'idno' not in session:
        return redirect(url_for('login'))
    
    laboratory = request.form.get('laboratory')
    feedback = request.form.get('feedback')
    user_id = session['idno']
    
    try:
        dbhelper.add_feedback(user_id, laboratory, feedback)
        flash('Thank you for your feedback!', 'success')
    except Exception as e:
        flash('Error submitting feedback. Please try again.', 'error')
        print(f"Error submitting feedback: {str(e)}")
    
    return redirect(url_for('sessions'))

# Add Lab Points route
@app.route('/add_lab_points', methods=['POST'])
@admin_required
def add_lab_points():
    try:
        data = request.get_json()
        idno = data.get('idno')
        # Use the points parameter if provided, otherwise default to 1
        points = data.get('points', 1)
        
        if not idno:
            return jsonify({'success': False, 'message': 'Student ID is required'}), 400
            
        # Add the specified points (default is 1)
        success = dbhelper.add_lab_points(idno, points)
        
        if success:
            return jsonify({'success': True, 'message': f'{points} point(s) added successfully'})
        return jsonify({'success': False, 'message': 'Failed to add lab points'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/convert_points_to_session', methods=['POST'])
@admin_required
def convert_points_to_session():
    try:
        data = request.get_json()
        idno = data.get('idno')
        
        if not idno:
            return jsonify({'success': False, 'message': 'Student ID is required'}), 400
            
        # Get current points
        student = dbhelper.get_user_by_id(idno)
        if not student or student['lab_points'] < 3:
            return jsonify({'success': False, 'message': 'Insufficient points'}), 400
            
        # Deduct 3 points and add a session
        success = dbhelper.convert_points_to_session(idno)
        
        if success:
            return jsonify({'success': True, 'message': 'Points converted to session successfully'})
        return jsonify({'success': False, 'message': 'Failed to convert points to session'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/reset_all_sessions', methods=['POST'])
def reset_all_sessions():
    if 'idno' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        dbhelper.reset_all_sessions()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/toggle_resources', methods=['POST'])
def toggle_resources():
    if 'idno' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        enabled = request.json.get('enabled', False)
        dbhelper.toggle_resources(enabled)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API endpoint for remaining sessions
@app.route('/api/remaining-sessions/<string:idno>')
def get_remaining_sessions(idno):
    try:
        user_data = dbhelper.get_user_by_id(idno)
        if user_data:
            remaining_sessions = user_data['remaining_sessions'] if user_data['remaining_sessions'] is not None else 30
            return jsonify({
                'remaining': remaining_sessions
            })
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(f"Error fetching remaining sessions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Reservation Management Routes
@app.route('/ad_reserve')
def ad_reserve():
    if 'username' not in session:
        flash('Please log in as admin to access this page.', 'error')
        return redirect(url_for('login'))
    
    # Get both reservations and logs
    reservations = dbhelper.get_pending_reservations()
    logs = dbhelper.get_reservation_logs()
    
    return render_template('ad_reserve.html', 
                         reservations=reservations,
                         logs=logs)

@app.route('/approve_reservation/<int:reservation_id>', methods=['POST'])
def approve_reservation(reservation_id):
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    # Get reservation details first
    reservation = dbhelper.get_reservation_by_id(reservation_id)
    if not reservation:
        return jsonify({'success': False, 'error': 'Reservation not found'}), 404
    
    # Print debug information
    print(f"Approving reservation #{reservation_id}")
    print(f"Reservation details: {reservation}")
    
    success, message = dbhelper.approve_reservation(reservation_id)
    print(f"Approval result: success={success}, message={message}")
    
    if success:
        # Log the approval action
        dbhelper.log_reservation_action(
            student_id=reservation['student_id'],
            laboratory_id=reservation['laboratory_id'],
            computer_no=reservation['computer_no'],
            action='approved',
            performed_by=session['username'],
            notes='Reservation approved'
        )
        return jsonify({'success': True, 'message': 'Reservation approved successfully'})
    
    return jsonify({'success': False, 'error': message}), 500

@app.route('/reject_reservation/<int:reservation_id>', methods=['POST'])
def reject_reservation(reservation_id):
    if 'username' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    # Get reservation details first
    reservation = dbhelper.get_reservation_by_id(reservation_id)
    if not reservation:
        return jsonify({'error': 'Reservation not found'}), 404
    
    # Get reason from JSON data or form data
    data = request.get_json()
    reason = None
    if data and 'reason' in data:
        reason = data.get('reason')
    else:
        reason = request.form.get('reason')
        
    if not reason:
        reason = 'No reason provided'
        
    success, message = dbhelper.reject_reservation(reservation_id, reason)
    if success:
        # Log the rejection action
        dbhelper.log_reservation_action(
            student_id=reservation['student_id'],
            laboratory_id=reservation['laboratory_id'],
            computer_no=reservation['computer_no'],
            action='rejected',
            performed_by=session['username'],
            notes=f'Rejected: {reason}'
        )
        return jsonify({'message': 'Reservation rejected successfully'})
    return jsonify({'error': 'Failed to reject reservation'}), 500

@app.route('/reservation_logs')
@admin_required
def reservation_logs():
    """View reservation logs."""
    logs = dbhelper.get_reservation_logs()
    return render_template('reservation_logs.html', logs=logs)

@app.route('/api/announcements')
@login_required
def get_announcements():
    """Get announcements for the current user."""
    announcements = dbhelper.get_user_announcements(session['idno'])
    return jsonify(announcements)

@app.route('/api/mark_announcement_read/<int:announcement_id>', methods=['POST'])
@login_required
def mark_announcement_read(announcement_id):
    """Mark an announcement as read."""
    try:
        dbhelper.mark_announcement_as_read(announcement_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/computers/<lab_id>')
def get_computers(lab_id):
    try:
        # Print for debugging
        print(f"Fetching computers for lab: {lab_id}")
        
        # Convert lab_id to int if it's a number as string, otherwise use as is
        lab_identifier = lab_id
        if isinstance(lab_id, str) and lab_id.isdigit():
            lab_identifier = int(lab_id)
            
        computers = dbhelper.get_computers_by_lab(lab_identifier)
        
        # Print for debugging
        print(f"Found {len(computers)} computers")
        print(f"Sample computer data: {computers[0] if computers else 'No computers found'}")
        
        return jsonify(computers)
    except Exception as e:
        print(f"Error fetching computers: {e}")
        return jsonify([])

@app.route('/api/create_lab_computers/<lab_id>', methods=['POST'])
def create_lab_computers(lab_id):
    try:
        # Print for debugging
        print(f"Creating computers for lab: {lab_id}")
        
        # Convert lab_id to int if it's a number as string, otherwise use as is
        lab_identifier = lab_id
        if isinstance(lab_id, str) and lab_id.isdigit():
            lab_identifier = int(lab_id)
        
        # First get the lab ID from the lab number if it's not a number
        if not isinstance(lab_identifier, int):
            # Get the lab ID from the lab number
            conn = dbhelper.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM laboratories WHERE number = ?", (lab_id,))
            lab = cursor.fetchone()
            
            if lab:
                lab_identifier = lab[0]
                print(f"Found lab ID {lab_identifier} for lab number {lab_id}")
            else:
                print(f"Lab not found for {lab_id}")
                return jsonify({'status': 'error', 'message': 'Laboratory not found'}), 404
            
            conn.close()
        
        # Create computers for this lab
        conn = dbhelper.get_db_connection()
        cursor = conn.cursor()
        
        # Check if there are computers already
        cursor.execute("SELECT COUNT(*) FROM computers WHERE laboratory_id = ?", (lab_identifier,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Lab {lab_id} already has {count} computers")
            conn.close()
            return jsonify({
                'status': 'success', 
                'message': f'Lab already has {count} computers',
                'count': count
            })
        
        # Create 30 computers for this lab
        print(f"Creating 30 computers for lab {lab_id} (ID: {lab_identifier})")
        for i in range(1, 31):
            cursor.execute("""
                INSERT INTO computers (laboratory_id, computer_no, is_available)
                VALUES (?, ?, 1)
            """, (lab_identifier, i))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success', 
            'message': 'Created 30 computers for lab',
            'count': 30
        })
    except Exception as e:
        print(f"Error creating computers: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/admin/computers/<lab_id>')
@admin_required
def get_computers_admin(lab_id):
    try:
        # Convert lab_id to int if it's a number as string, otherwise use as is
        lab_identifier = lab_id
        if isinstance(lab_id, str) and lab_id.isdigit():
            lab_identifier = int(lab_id)
            
        computers = dbhelper.get_computers_by_lab(lab_identifier)
        return jsonify(computers)
    except Exception as e:
        print(f"Error fetching computers: {e}")
        return jsonify([])

@app.route('/update_computer_status/<int:computer_id>', methods=['POST'])
@admin_required
def update_computer_status_route(computer_id):
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
        
    data = request.get_json()
    is_available = data.get('is_available', False)
    admin_id = session.get('username')  # Use the admin username from session
    
    success, message = dbhelper.update_computer_status(computer_id, is_available, admin_id)
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': message}), 400

@app.route('/check_reservation_status')
@login_required
def check_reservation_status():
    student_id = session.get('idno')
    
    # Get the user's sit-in status using our helper function
    sit_in_status = dbhelper.check_active_sitin_status(student_id)
    
    # Get more detailed status info for the frontend
    has_pending = dbhelper.check_user_has_pending_reservation(student_id)
    has_approved = dbhelper.check_user_has_approved_reservation(student_id)
    
    # Use the helper function to determine if form should be disabled
    should_disable, reason = dbhelper.should_disable_reservation_form(student_id)
    
    # Debug output
    print(f"Checking reservation status for student {student_id}")
    print(f"Sit-in status: {sit_in_status}")
    print(f"Has pending reservation: {has_pending}")
    print(f"Has approved reservation: {has_approved}")
    print(f"Should disable form: {should_disable}")
    if reason:
        print(f"Reason: {reason}")
    
    return jsonify({
        'can_reserve': not should_disable,
        'has_pending_reservation': has_pending,
        'has_approved_reservation': has_approved,
        'in_active_session': sit_in_status['has_active_session'],
        'was_logged_out': sit_in_status['was_logged_out'],
        'completed_sessions': sit_in_status['completed_sessions'],
        'message': reason
    })

# Student Reservation Routes
@app.route('/reserve_computer', methods=['POST'])
@login_required
def reserve_computer():
    try:
        # Get form data
        laboratory_id = request.form.get('laboratory_id')
        computer_no = request.form.get('computer_no', type=int)
        purpose = request.form.get('purpose')
        datetime_str = request.form.get('datetime')
        student_id = session.get('idno')  # Get student ID from session
        
        # Validate all required fields
        if not all([laboratory_id, computer_no, purpose, datetime_str, student_id]):
            return jsonify({
                'status': 'error',
                'message': 'All fields are required'
            }), 400
        
        # Create the reservation
        success, message = dbhelper.create_reservation(
            student_id=student_id,
            laboratory_id=laboratory_id,
            computer_no=computer_no,
            purpose=purpose,
            datetime=datetime_str
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Reservation request submitted successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
            
    except Exception as e:
        print(f"Error in reserve_computer: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/api/laboratories')
def get_laboratories():
    try:
        # Print schema for debugging
        with sqlite3.connect('sitinmonitor.db') as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(laboratory_status)")
            print("Laboratory status table schema:", cursor.fetchall())
            
            # Add missing columns if needed
            for col in ['reason', 'start_date', 'end_date', 'notes', 'other_reason']:
                try:
                    cursor.execute(f"ALTER TABLE laboratory_status ADD COLUMN {col} TEXT")
                    print(f"Added missing column {col} to laboratory_status table")
                except sqlite3.OperationalError as e:
                    # Column likely already exists
                    if "duplicate column name" in str(e):
                        pass
                    else:
                        print(f"Error adding column {col}: {e}")
            conn.commit()
            
        # Get laboratories (will check schedule status against current time)
        laboratories = dbhelper.get_laboratories()
        
        # Refresh any active schedules
        dbhelper.refresh_lab_schedules()
        
        return jsonify(laboratories)
    except Exception as e:
        print(f"Error in get_laboratories: {e}")
        return jsonify([])

@app.route('/reset_all_points', methods=['POST'])
@admin_required
def reset_all_points():
    try:
        success = dbhelper.reset_all_points()
        if success:
            return jsonify({'success': True, 'message': 'All points reset successfully'})
        return jsonify({'success': False, 'message': 'Failed to reset points'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Laboratory Status API Routes
@app.route('/update_lab_status', methods=['POST'])
def update_lab_status():
    if 'username' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    try:
        data = request.json
        lab_number = data.get('labNumber')
        is_available = data.get('available', False)
        admin_username = session.get('username')
        
        if not lab_number:
            return jsonify({'status': 'error', 'message': 'Lab number is required'}), 400
        
        # Update lab status in the database
        success, message = dbhelper.update_lab_status(lab_number, is_available, admin_username)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Laboratory status updated'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/lab_statuses', methods=['GET'])
def get_lab_statuses():
    try:
        # Refresh any lab schedules first
        dbhelper.refresh_lab_schedules()
        
        # Get lab statuses from database
        lab_statuses = dbhelper.get_lab_statuses()
        return jsonify(lab_statuses)
    except Exception as e:
        print(f"Error fetching lab statuses: {e}")
        return jsonify([]), 500

@app.route('/update_lab_schedule', methods=['POST'])
def update_lab_schedule():
    if 'username' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    try:
        data = request.json
        lab_number = data.get('labNumber')
        is_available = data.get('available', True)
        admin_username = session.get('username')
        
        # Get additional schedule details
        reason = data.get('reason', '')
        start_date = data.get('startDate', '')
        end_date = data.get('endDate', '')
        notes = data.get('notes', '')
        other_reason = data.get('otherReason', '')
        
        if not lab_number:
            return jsonify({'status': 'error', 'message': 'Lab number is required'}), 400
        
        # Update lab status in the database with schedule details
        success, message = dbhelper.update_lab_schedule(
            lab_number, 
            is_available, 
            admin_username,
            reason,
            start_date, 
            end_date, 
            notes,
            other_reason
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Laboratory schedule updated'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Resource routes
@app.route('/upload_resource', methods=['POST'])
@admin_required
def upload_resource():
    if 'resource_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    file = request.files['resource_file']
    
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if file and allowed_file(file.filename):
        # Securely generate filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Get form data
        title = request.form.get('resource_title')
        category = request.form.get('resource_category')
        description = request.form.get('resource_description', '')
        
        # Ensure category folder exists
        category_folder = os.path.join(app.config['RESOURCE_FOLDER'], category)
        os.makedirs(category_folder, exist_ok=True)
        
        # Save the file in the category folder
        file_path = os.path.join(category_folder, unique_filename)
        file.save(file_path)
        
        # For database, store relative path from resource folder
        relative_path = os.path.join(category, unique_filename)
        
        # Print debug info
        print(f"Uploading resource: {title}")
        print(f"Category: {category}")
        print(f"File path: {file_path}")
        print(f"Relative path: {relative_path}")
        
        # Save metadata to database
        resource_id = dbhelper.add_resource(
            title=title,
            description=description,
            category=category,
            file_path=relative_path,
            original_filename=original_filename,
            file_type=file_extension,
            file_size=os.path.getsize(file_path),
            uploaded_by=session.get('username', 'admin')
        )
        
        if resource_id:
            flash('Resource uploaded successfully!', 'success')
        else:
            # Delete the file if database insert failed
            os.remove(file_path)
            flash('Failed to upload resource', 'danger')
    else:
        flash('File type not allowed', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/download_resource/<int:resource_id>')
def download_resource(resource_id):
    # Get resource info from database
    resource = dbhelper.get_resource_by_id(resource_id)
    
    if not resource:
        flash('Resource not found', 'danger')
        return redirect(url_for('labrules'))
    
    # Full path to the file
    file_path = os.path.join(app.config['RESOURCE_FOLDER'], resource['file_path'])
    
    # Check if file exists
    if not os.path.exists(file_path):
        flash('Resource file not found', 'danger')
        return redirect(url_for('labrules'))
    
    # Return the file as an attachment (for download)
    return send_file(
        file_path,
        as_attachment=True,
        download_name=resource['original_filename']
    )

@app.route('/delete_resource/<int:resource_id>', methods=['POST'])
@admin_required
def delete_resource(resource_id):
    try:
        # Get resource info from database
        resource = dbhelper.get_resource_by_id(resource_id)
        
        if not resource:
            return jsonify({'success': False, 'message': 'Resource not found'})
        
        # Delete the file
        file_path = os.path.join(app.config['RESOURCE_FOLDER'], resource['file_path'])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        success = dbhelper.delete_resource(resource_id)
        
        if success:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Failed to delete from database'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/download/<category>')
@login_required
def download_category_resources(category):
    # Get resources for the specific category
    try:
        resources = dbhelper.get_resources_by_category(category)
    except Exception as e:
        print(f"Error retrieving resources by category: {e}")
        resources = []
    
    # Check if resources are enabled
    resources_enabled = dbhelper.get_resources_enabled()
    if not resources_enabled:
        flash('Resource downloads are currently disabled', 'warning')
        return redirect(url_for('labrules'))
    
    # Get user data safely
    try:
        username = dbhelper.get_user_by_id(session['idno'])
    except Exception as e:
        print(f"Error retrieving user data: {e}")
        flash('Error loading user data', 'error')
        return redirect(url_for('labrules'))
    
    return render_template('download_resources.html', 
                          resources=resources, 
                          category=category,
                          username=username)

# Make sure the resource directory exists
os.makedirs(app.config['RESOURCE_FOLDER'], exist_ok=True)

@app.route('/api/check_active_session/<string:student_id>')
@login_required
def check_active_session(student_id):
    """
    Check if a student ID is in the list of current sit-in students.
    
    This endpoint helps the frontend validate if a user is already in an active session
    before allowing them to make a reservation.
    
    It also checks if the user had a recently ended session to help refresh the reservation history.
    """
    try:
        # Get all currently active sit-in students
        active_students = dbhelper.get_current_sit_in_students()
        
        # Check if the given student ID is in the active students list
        is_active = any(student['idno'] == student_id for student in active_students)
        
        # If active, get the session details
        active_session_details = None
        if is_active:
            for student in active_students:
                if student['idno'] == student_id:
                    active_session_details = {
                        'laboratory': student['laboratory'],
                        'time_in': student['time_in'],
                        'purpose': student['purpose']
                    }
                    break
        
        # Check if student had a recently ended session in the last 5 minutes
        conn = dbhelper.get_db_connection()
        cursor = conn.cursor()
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Check for sessions that ended in the last 5 minutes
        five_mins_ago = (datetime.now() - timedelta(minutes=5)).strftime("%H:%M:%S")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM SIT_IN_HISTORY 
            WHERE idno = ? 
            AND date = ? 
            AND time_out != time_in 
            AND time_out BETWEEN ? AND ?
        """, (student_id, current_date, five_mins_ago, current_time))
        
        recently_ended_count = cursor.fetchone()[0]
        session_ended = recently_ended_count > 0
        
        # If a session has recently ended, also fetch the updated reservation history
        updated_reservation_history = None
        if session_ended:
            print(f"Student {student_id} had a session end recently. Fetching updated reservation history.")
            updated_reservation_history = dbhelper.get_user_reservations(student_id)
            
            # Convert the full objects to a simpler format for JSON serialization
            if updated_reservation_history:
                simplified_history = []
                for res in updated_reservation_history:
                    simplified_history.append({
                        'id': res.get('id'),
                        'laboratory': res.get('laboratory'),
                        'computer_no': res.get('computer_no'),
                        'purpose': res.get('purpose'),
                        'datetime': res.get('datetime'),
                        'status': res.get('status'),
                        'created_at': res.get('created_at'),
                        'session_end_time': res.get('session_end_time', '-'),
                        'rejection_reason': res.get('rejection_reason', '-')
                    })
                updated_reservation_history = simplified_history
        
        conn.close()
        
        # Return the result as JSON
        return jsonify({
            'is_active': is_active,
            'session_details': active_session_details,
            'student_id': student_id,
            'session_ended': session_ended,
            'recently_ended_count': recently_ended_count,
            'updated_reservation_history': updated_reservation_history
        })
    except Exception as e:
        print(f"Error checking active session for student {student_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'is_active': False,
            'error': str(e),
            'student_id': student_id,
            'session_ended': False
        })

if __name__ == "__main__":
    app.run(debug=True)