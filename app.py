from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import sqlite3  
import os
from werkzeug.utils import secure_filename
import dbhelper
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "database1234!"
app.config['UPLOAD_FOLDER'] = 'static/images/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialize database on startup
dbhelper.initialize_database()

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
    
    # Get all students for the leaderboard
    students = dbhelper.get_all_students()
    
    # Get resource status
    resources_enabled = dbhelper.get_resources_enabled()
    
    return render_template('admin_dashboard.html',
                         students_registered=students_registered,
                         currently_sit_in=currently_sit_in,
                         total_sit_in=total_sit_in,
                         purposes_labels=purposes_labels,
                         purposes_data=purposes_counts,
                         students=students,
                         resources_enabled=resources_enabled)

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
        # Update the sit-in record with end time
        dbhelper.end_sit_in_session(idno)
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

# Sessions route
@app.route('/sessions')
def sessions():
    if 'idno' not in session:
        flash('Please log in to view your sessions.')
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
        'avatar_filename': session.get('avatar_filename', 'default.png'),
        'remaining_sessions': remaining_sessions,
        'total_sessions': total_sessions
    }
    
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
    
    return render_template('reservations.html', 
                         username=user,
                         sessions=sessions_data)

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
def add_lab_points():
    if "username" not in session:
        return jsonify({"success": False, "message": "Not authorized"}), 401
    
    data = request.get_json()
    idno = data.get('idno')
    
    if not idno:
        return jsonify({"success": False, "message": "Student ID is required"}), 400
    
    try:
        # Add 3 points to the student
        dbhelper.add_lab_points(idno, 3)
        return jsonify({"success": True, "message": "Points added successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

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
            remaining_sessions = user_data[8] if user_data[8] is not None else 30
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
    reservations = dbhelper.get_pending_reservations()
    return render_template('ad_reserve.html', 
                         reservations=reservations)

@app.route('/approve_reservation/<int:reservation_id>', methods=['POST'])
@admin_required
def approve_reservation_route(reservation_id):
    try:
        # Get reservation details first
        reservation = dbhelper.get_reservation_by_id(reservation_id)
        if not reservation:
            flash('Reservation not found.', 'error')
            return jsonify({'success': False, 'message': 'Reservation not found'}), 404

        # Approve the reservation
        success, message = dbhelper.approve_reservation(reservation_id)
        if not success:
            flash(f'Error approving reservation: {message}', 'error')
            return jsonify({'success': False, 'message': message}), 400
        
        # Create announcement for the student
        message = f"Your reservation for Laboratory {reservation['laboratory_id']}, Computer {reservation['computer_no']} has been approved."
        dbhelper.create_announcement(reservation['student_id'], message, 'success')
        
        # Log the action
        dbhelper.create_reservation_log(
            reservation_id=reservation_id,
            action='approved',
            performed_by=session['username'],
            notes='Reservation approved by administrator'
        )
        
        flash('Reservation approved successfully!', 'success')
        return jsonify({'success': True, 'message': 'Reservation approved successfully'})
    except Exception as e:
        flash(f'Error approving reservation: {str(e)}', 'error')
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/reject_reservation/<int:reservation_id>', methods=['POST'])
@admin_required
def reject_reservation_route(reservation_id):
    try:
        # Get reservation details first
        reservation = dbhelper.get_reservation_by_id(reservation_id)
        if not reservation:
            flash('Reservation not found.', 'error')
            return jsonify({'success': False, 'message': 'Reservation not found'}), 404

        # Get rejection reason from request
        reason = request.json.get('reason', 'No reason provided')
        
        # Reject the reservation
        success, message = dbhelper.reject_reservation(reservation_id)
        if not success:
            flash(f'Error rejecting reservation: {message}', 'error')
            return jsonify({'success': False, 'message': message}), 400
        
        # Create announcement for the student
        message = f"Your reservation for Laboratory {reservation['laboratory_id']}, Computer {reservation['computer_no']} has been rejected. Reason: {reason}"
        dbhelper.create_announcement(reservation['student_id'], message, 'danger')
        
        # Log the action
        dbhelper.create_reservation_log(
            reservation_id=reservation_id,
            action='rejected',
            performed_by=session['username'],
            notes=f'Reservation rejected by administrator. Reason: {reason}'
        )
        
        flash('Reservation rejected successfully!', 'success')
        return jsonify({'success': True, 'message': 'Reservation rejected successfully'})
    except Exception as e:
        flash(f'Error rejecting reservation: {str(e)}', 'error')
        return jsonify({'success': False, 'message': str(e)}), 500

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

@app.route('/api/computers/<int:lab_id>')
@admin_required
def get_computers_route(lab_id):
    computers = dbhelper.get_computers_by_lab(lab_id)
    return jsonify(computers)

@app.route('/update_computer_status/<int:computer_id>', methods=['POST'])
@admin_required
def update_computer_status_route(computer_id):
    data = request.get_json()
    is_available = data.get('is_available', False)
    
    success, message = dbhelper.update_computer_status(computer_id, is_available)
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': message}), 400

# Student Reservation Routes
@app.route('/reserve_computer', methods=['POST'])
@login_required
def reserve_computer():
    try:
        # Get form data
        laboratory_id = request.form.get('laboratory_id', type=int)
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
        laboratories = dbhelper.get_laboratories()
        return jsonify(laboratories)
    except Exception as e:
        print(f"Error fetching laboratories: {e}")
        return jsonify([])

@app.route('/api/computers/<int:lab_id>')
def get_computers(lab_id):
    try:
        computers = dbhelper.get_computers_by_lab(lab_id)
        return jsonify(computers)
    except Exception as e:
        print(f"Error fetching computers: {e}")
        return jsonify([])

if __name__ == "__main__":
    app.run(debug=True)