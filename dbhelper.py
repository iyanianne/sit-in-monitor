import sqlite3
import os
from datetime import datetime

def get_db_connection():
    try:
        conn = sqlite3.connect('sitinmonitor.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        raise

def add_user(idno, lastname, fname, mname, course, yrlvl, email, username, password):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO USERS (idno, lastname, fname, mname, course, yrlvl, email, username, password, remaining_sessions, total_sessions) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (idno, lastname, fname, mname, course, yrlvl, email, username, password, 30, 30))
        conn.commit()

def get_user_by_idno_or_username_and_password(idno, username, password):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                idno,
                lastname,
                fname,
                mname,
                course,
                yrlvl,
                email,
                avatar_filename,
                username,
                password,
                COALESCE(remaining_sessions, 30) as remaining_sessions,
                COALESCE(total_sessions, 30) as total_sessions
            FROM USERS 
            WHERE (idno=? OR username=?) AND password=?
        """, (idno, username, password))
        return cursor.fetchone()

def get_admin_by_username_and_password(username, password):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ADMIN WHERE username=? AND password=?", (username, password))
        return cursor.fetchone()

def get_user_by_id(idno):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                idno,
                lastname,
                fname,
                mname,
                course,
                yrlvl,
                email,
                avatar_filename,
                COALESCE(remaining_sessions, 30) as remaining_sessions,
                COALESCE(total_sessions, 30) as total_sessions
            FROM USERS 
            WHERE idno=?
        """, (idno,))
        return cursor.fetchone()

def update_user(idno, lastname, fname, mname, course, yrlvl, email):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE USERS SET lastname = ?, fname = ?, mname = ?, course = ?, yrlvl = ?, email = ? WHERE idno = ?
        """, (lastname, fname, mname, course, yrlvl, email, idno))
        conn.commit()

def update_user_avatar(idno, avatar_filename):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE USERS SET avatar_filename = ? WHERE idno = ?", (avatar_filename, idno))
        conn.commit()

def get_all_students():
    with sqlite3.connect("sitinmonitor.db") as conn:
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                idno, 
                lastname,
                fname,
                mname,
                course,
                yrlvl,
                email,
                COALESCE(lab_points, 0) as lab_points,
                COALESCE(remaining_sessions, 30) as remaining_sessions,
                COALESCE(total_sessions, 30) as total_sessions
            FROM USERS
            WHERE username NOT IN (SELECT username FROM ADMIN)
            ORDER BY lab_points DESC, lastname, fname
        """)
        
        students = cursor.fetchall()
        return [dict(row) for row in students]  # Convert rows to dictionary

def count_registered_students():
    conn = sqlite3.connect("sitinmonitor.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM USERS")
    result = cursor.fetchone()[0]
    conn.close()
    return result

def get_student_sessions(idno):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                idno,
                remaining_sessions,
                total_sessions
            FROM USERS 
            WHERE idno=?
        """, (idno,))
        return cursor.fetchone()

def get_student_history(idno):
    """
    Get the complete sit-in history for a student including all session details
    """
    with sqlite3.connect("sitinmonitor.db") as conn:
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                SIT_IN_HISTORY.idno,
                SIT_IN_HISTORY.date,
                SIT_IN_HISTORY.time_in,
                SIT_IN_HISTORY.time_out,
                SIT_IN_HISTORY.purpose,
                SIT_IN_HISTORY.laboratory,
                USERS.fname || ' ' || COALESCE(USERS.mname, '') || ' ' || USERS.lastname as student_name,
                USERS.course
            FROM SIT_IN_HISTORY
            JOIN USERS ON SIT_IN_HISTORY.idno = USERS.idno
            WHERE SIT_IN_HISTORY.idno = ?
            ORDER BY SIT_IN_HISTORY.date DESC, SIT_IN_HISTORY.time_in DESC
        """, (idno,))
        
        history = cursor.fetchall()
        return [dict(row) for row in history]  # Convert rows to dictionaries

def update_student_sessions(idno, remaining_sessions):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE USERS 
            SET remaining_sessions = ? 
            WHERE idno = ?
        """, (remaining_sessions, idno))
        conn.commit()

def add_sit_in_history(idno, date, time_in, time_out, purpose, laboratory):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO SIT_IN_HISTORY 
            (idno, date, time_in, time_out, purpose, laboratory) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (idno, date, time_in, time_out, purpose, laboratory))
        conn.commit()

def count_currently_sit_in():
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM SIT_IN_HISTORY 
            WHERE date = date('now')
        """)
        return cursor.fetchone()[0]

def count_total_sit_in():
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM SIT_IN_HISTORY")
        return cursor.fetchone()[0]

def get_sit_in_purposes_distribution():
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT purpose, COUNT(*) as count
            FROM SIT_IN_HISTORY
            GROUP BY purpose
            ORDER BY count DESC
        """)
        return cursor.fetchall()

def initialize_student_sessions(idno):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE USERS 
            SET remaining_sessions = 30, total_sessions = 30 
            WHERE idno = ? AND (remaining_sessions IS NULL OR remaining_sessions = 0)
        """, (idno,))
        conn.commit()

def decrement_student_session(idno):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE USERS 
            SET remaining_sessions = remaining_sessions - 1 
            WHERE idno = ? AND remaining_sessions > 0
        """, (idno,))
        conn.commit()

def update_sit_in_status(idno, purpose, laboratory):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        cursor.execute("""
            INSERT INTO SIT_IN_HISTORY (idno, date, time_in, time_out, purpose, laboratory)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (idno, current_date, current_time, current_time, purpose, laboratory))
        conn.commit()

def get_current_sit_in_students():
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute("""
            SELECT 
                u.idno,
                u.lastname || ', ' || u.fname || ' ' || u.mname as name,
                u.remaining_sessions,
                u.total_sessions,
                h.purpose,
                h.laboratory,
                h.time_in
            FROM USERS u
            JOIN SIT_IN_HISTORY h ON u.idno = h.idno
            WHERE h.date = ? AND h.time_in = h.time_out
        """, (current_date,))
        
        results = cursor.fetchall()
        students = []
        for row in results:
            students.append({
                'idno': row[0],
                'name': row[1],
                'remaining_sessions': row[2],
                'total_sessions': row[3],
                'purpose': row[4],
                'laboratory': row[5],
                'time_in': row[6]
            })
        return students

def end_sit_in_session(idno):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Update the session end time
        cursor.execute("""
            UPDATE SIT_IN_HISTORY 
            SET time_out = ?
            WHERE idno = ? AND date = ? AND time_in = time_out
        """, (current_time, idno, current_date))
        
        # Only decrement if we actually ended a session (i.e., if the update affected a row)
        if cursor.rowcount > 0:
            cursor.execute("""
                UPDATE USERS 
                SET remaining_sessions = remaining_sessions - 1 
                WHERE idno = ? AND remaining_sessions > 0
            """, (idno,))
        
        conn.commit()

def get_sit_in_reports():
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                h.idno,
                u.lastname || ', ' || u.fname || ' ' || u.mname as name,
                h.date,
                h.time_in,
                h.time_out,
                h.purpose,
                h.laboratory,
                u.remaining_sessions
            FROM SIT_IN_HISTORY h
            JOIN USERS u ON h.idno = u.idno
            WHERE h.time_in != h.time_out
            ORDER BY h.date DESC, h.time_in DESC
        """)
        
        results = cursor.fetchall()
        reports = []
        for row in results:
            reports.append({
                'idno': row[0],
                'name': row[1],
                'date': row[2],
                'time_in': row[3],
                'time_out': row[4],
                'purpose': row[5],
                'laboratory': row[6],
                'remaining_sessions': row[7] if row[7] is not None else 30
            })
        return reports

def get_sit_in_records():
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                h.idno,
                u.lastname || ', ' || u.fname || ' ' || COALESCE(u.mname, '') as name,
                h.date,
                h.time_in,
                h.time_out,
                h.purpose,
                h.laboratory,
                u.course,
                u.yrlvl,
                u.remaining_sessions,
                u.total_sessions
            FROM SIT_IN_HISTORY h
            JOIN USERS u ON h.idno = u.idno
            ORDER BY h.date DESC, h.time_in DESC
        """)
        
        results = cursor.fetchall()
        records = []
        for row in results:
            # Calculate duration if time_out is different from time_in
            duration = "N/A"
            if row[3] != row[4]:
                try:
                    time_in = datetime.strptime(row[3], "%H:%M:%S")
                    time_out = datetime.strptime(row[4], "%H:%M:%S")
                    diff = time_out - time_in
                    hours, remainder = divmod(diff.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    if hours > 0:
                        duration = f"{hours}h {minutes}m"
                    else:
                        duration = f"{minutes}m {seconds}s"
                except Exception as e:
                    duration = "N/A"
            else:
                duration = "Active Session"
            
            # Ensure all values are properly handled to avoid undefined in JSON
            records.append({
                'idno': str(row[0]) if row[0] is not None else "",
                'name': str(row[1]) if row[1] is not None else "",
                'date': str(row[2]) if row[2] is not None else "",
                'time_in': str(row[3]) if row[3] is not None else "",
                'time_out': str(row[4]) if row[4] is not None else "",
                'purpose': str(row[5]) if row[5] is not None else "",
                'laboratory': str(row[6]) if row[6] is not None else "",
                'course': str(row[7]) if row[7] is not None else "",
                'year_level': str(row[8]) if row[8] is not None else "",
                'remaining_sessions': int(row[9]) if row[9] is not None else 30,
                'total_sessions': int(row[10]) if row[10] is not None else 30,
                'duration': duration
            })
        return records

def reset_student_sessions(idno):
    """Reset a student's sessions to 30."""
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE USERS 
            SET remaining_sessions = 30, total_sessions = 30 
            WHERE idno = ?
        """, (idno,))
        conn.commit()
        return True

def get_sit_in_leaderboard():
    """Get students sorted by their sit-in count."""
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                u.idno,
                u.lastname || ', ' || u.fname || ' ' || COALESCE(u.mname, '') as name,
                u.course,
                COUNT(h.idno) as sit_in_count
            FROM USERS u
            LEFT JOIN SIT_IN_HISTORY h ON u.idno = h.idno
            WHERE u.username NOT IN (SELECT username FROM ADMIN)
            GROUP BY u.idno, u.lastname, u.fname, u.mname, u.course
            ORDER BY sit_in_count DESC
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        leaderboard = []
        for row in results:
            leaderboard.append({
                'idno': str(row[0]),
                'name': str(row[1]),
                'course': str(row[2]),
                'sit_in_count': int(row[3])
            })
        return leaderboard

def add_feedback(user_id, laboratory, feedback):
    """
    Add a feedback record to the database
    """
    try:
        conn = sqlite3.connect("sitinmonitor.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO FEEDBACK (user_id, laboratory, feedback, created_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (user_id, laboratory, feedback))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding feedback: {str(e)}")
        raise e

def get_all_feedbacks():
    """Get all feedback records with student details."""
    with sqlite3.connect("sitinmonitor.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                f.id,
                f.user_id,
                f.laboratory,
                f.feedback,
                f.created_at,
                u.fname || ' ' || COALESCE(u.mname, '') || ' ' || u.lastname as student_name,
                u.course
            FROM FEEDBACK f
            JOIN USERS u ON f.user_id = u.idno
            ORDER BY f.created_at DESC
        """)
        feedbacks = cursor.fetchall()
        return [dict(row) for row in feedbacks]

def add_lab_points(idno, points):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE USERS 
            SET lab_points = COALESCE(lab_points, 0) + ?
            WHERE idno = ?
        """, (points, idno))
        conn.commit()
        return True

def get_student_lab_points(idno):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(lab_points, 0) as lab_points
            FROM USERS 
            WHERE idno = ?
        """, (idno,))
        result = cursor.fetchone()
        return result[0] if result else 0

def get_lab_reports():
    """Get detailed reports of laboratory usage."""
    with sqlite3.connect("sitinmonitor.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                h.idno,
                u.lastname || ', ' || u.fname || ' ' || COALESCE(u.mname, '') as name,
                h.date,
                h.time_in,
                h.time_out,
                h.purpose,
                h.laboratory,
                u.remaining_sessions,
                u.total_sessions,
                CASE 
                    WHEN h.time_in != h.time_out THEN
                        CASE
                            WHEN strftime('%s', h.time_out) - strftime('%s', h.time_in) >= 3600 THEN
                                (strftime('%H', strftime('%s', h.time_out) - strftime('%s', h.time_in), 'unixepoch') || 'h ' ||
                                 strftime('%M', strftime('%s', h.time_out) - strftime('%s', h.time_in), 'unixepoch') || 'm')
                            ELSE
                                (strftime('%M', strftime('%s', h.time_out) - strftime('%s', h.time_in), 'unixepoch') || 'm ' ||
                                 strftime('%S', strftime('%s', h.time_out) - strftime('%s', h.time_in), 'unixepoch') || 's')
                        END
                    ELSE 'Active Session'
                END as duration
            FROM SIT_IN_HISTORY h
            JOIN USERS u ON h.idno = u.idno
            ORDER BY h.date DESC, h.time_in DESC
        """)
        reports = cursor.fetchall()
        return [dict(row) for row in reports]

def reset_all_sessions():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE USERS SET remaining_sessions = 30")
        conn.commit()
    finally:
        conn.close()

def toggle_resources(enabled):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Create the settings table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SETTINGS (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Update or insert the resources_enabled setting
        cursor.execute("""
            INSERT OR REPLACE INTO SETTINGS (key, value)
            VALUES ('resources_enabled', ?)
        """, (str(enabled).lower(),))
        
        conn.commit()
    finally:
        conn.close()

def get_resources_enabled():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Create the settings table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SETTINGS (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Try to get the resources_enabled setting
        cursor.execute("SELECT value FROM SETTINGS WHERE key = 'resources_enabled'")
        result = cursor.fetchone()
        
        # If no setting exists, create it with default value False
        if not result:
            cursor.execute("""
                INSERT INTO SETTINGS (key, value)
                VALUES ('resources_enabled', 'false')
            """)
            conn.commit()
            return False
            
        return result[0].lower() == 'true'
    finally:
        conn.close()

# Reservation related functions
def create_reservation(student_id, laboratory_id, computer_no, purpose, datetime):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if the computer exists in the specified laboratory
        cursor.execute("""
            SELECT is_available FROM computers 
            WHERE laboratory_id = ? AND computer_no = ?
        """, (laboratory_id, computer_no))
        result = cursor.fetchone()
        
        if not result:
            return False, "Computer not found in the specified laboratory"
            
        if not result[0]:
            return False, "Computer is not available"
            
        # Check if there's any overlapping reservation for this computer
        cursor.execute("""
            SELECT id FROM reservations 
            WHERE laboratory_id = ? 
            AND computer_no = ? 
            AND datetime = ?
            AND status != 'rejected'
        """, (laboratory_id, computer_no, datetime))
        
        if cursor.fetchone():
            return False, "This computer is already reserved for the selected time"
            
        # Create the reservation
        cursor.execute("""
            INSERT INTO reservations 
            (student_id, laboratory_id, computer_no, purpose, datetime, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (student_id, laboratory_id, computer_no, purpose, datetime))
        
        conn.commit()
        return True, "Reservation created successfully"
    except Exception as e:
        print(f"Error creating reservation: {e}")
        return False, "Failed to create reservation"
    finally:
        conn.close()

def get_pending_reservations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                r.id,
                u.fname || ' ' || COALESCE(u.mname, '') || ' ' || u.lastname as student_name,
                u.course,
                r.laboratory_id,
                r.computer_no,
                r.purpose,
                r.datetime,
                r.status
            FROM reservations r
            JOIN USERS u ON r.student_id = u.idno
            ORDER BY 
                CASE r.status
                    WHEN 'pending' THEN 1
                    WHEN 'approved' THEN 2
                    WHEN 'rejected' THEN 3
                END,
                r.datetime DESC
        """)
        
        reservations = []
        for row in cursor.fetchall():
            reservations.append({
                'id': row[0],
                'student_name': row[1],
                'course': row[2],
                'laboratory': row[3],
                'computer_no': row[4],
                'purpose': row[5],
                'datetime': row[6],
                'status': row[7]
            })
        
        return reservations
    except Exception as e:
        print(f"Error fetching reservations: {e}")
        return []
    finally:
        conn.close()

def approve_reservation(reservation_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get reservation details
        cursor.execute("""
            SELECT laboratory_id, computer_no, datetime
            FROM reservations
            WHERE id = ?
        """, (reservation_id,))
        reservation = cursor.fetchone()
        
        if not reservation:
            return False, "Reservation not found"
        
        # Check if computer is still available
        cursor.execute("""
            SELECT is_available 
            FROM computers 
            WHERE laboratory_id = ? AND computer_no = ?
        """, (reservation[0], reservation[1]))
        computer = cursor.fetchone()
        
        if not computer or not computer[0]:
            return False, "Computer is no longer available"
            
        # Update reservation status
        cursor.execute("""
            UPDATE reservations
            SET status = 'approved'
            WHERE id = ?
        """, (reservation_id,))
        
        # Update computer availability
        cursor.execute("""
            UPDATE computers
            SET is_available = 0
            WHERE laboratory_id = ? AND computer_no = ?
        """, (reservation[0], reservation[1]))
        
        # Update any other pending reservations for the same computer and time
        cursor.execute("""
            UPDATE reservations
            SET status = 'rejected'
            WHERE id != ? 
            AND laboratory_id = ? 
            AND computer_no = ? 
            AND datetime = ?
            AND status = 'pending'
        """, (reservation_id, reservation[0], reservation[1], reservation[2]))
        
        conn.commit()
        return True, "Reservation approved successfully"
    except Exception as e:
        print(f"Error approving reservation: {e}")
        return False, "Failed to approve reservation"
    finally:
        conn.close()

def reject_reservation(reservation_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE reservations
            SET status = 'rejected'
            WHERE id = ?
        """, (reservation_id,))
        
        conn.commit()
        return True, "Reservation rejected successfully"
    except Exception as e:
        print(f"Error rejecting reservation: {e}")
        return False, "Failed to reject reservation"
    finally:
        conn.close()

def get_laboratories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, number FROM laboratories")
        
        laboratories = []
        for row in cursor.fetchall():
            laboratories.append({
                'id': row[0],
                'number': row[1]
            })
        
        return laboratories
    except Exception as e:
        print(f"Error fetching laboratories: {e}")
        return []
    finally:
        conn.close()

def get_computers_by_lab(laboratory_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, computer_no, is_available
            FROM computers
            WHERE laboratory_id = ?
            ORDER BY computer_no
        """, (laboratory_id,))
        
        computers = []
        for row in cursor.fetchall():
            computers.append({
                'id': row[0],
                'number': row[1],
                'is_available': bool(row[2])
            })
        
        return computers
    except Exception as e:
        print(f"Error fetching computers: {e}")
        return []
    finally:
        conn.close()

def update_computer_status(computer_id, is_available):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get computer details first
        cursor.execute("""
            SELECT laboratory_id, computer_no
            FROM computers
            WHERE id = ?
        """, (computer_id,))
        computer = cursor.fetchone()
        
        if not computer:
            return False, "Computer not found"
        
        # If marking as unavailable, check for any pending reservations
        if not is_available:
            cursor.execute("""
                UPDATE reservations
                SET status = 'rejected'
                WHERE laboratory_id = ?
                AND computer_no = ?
                AND status = 'pending'
            """, (computer[0], computer[1]))
        
        # Update computer status
        cursor.execute("""
            UPDATE computers
            SET is_available = ?
            WHERE id = ?
        """, (1 if is_available else 0, computer_id))
        
        conn.commit()
        return True, "Computer status updated successfully"
    except Exception as e:
        print(f"Error updating computer status: {e}")
        return False, "Failed to update computer status"
    finally:
        conn.close()

def initialize_database():
    """Initialize the database with required tables and initial data."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Read and execute the schema.sql file
        with open('schema.sql', 'r') as f:
            schema = f.read()
            cursor.executescript(schema)

        conn.commit()
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        conn.close()

def create_announcement(student_id, message, type='info'):
    """Create a new announcement for a student."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO announcements (student_id, message, type)
        VALUES (?, ?, ?)
    """, (student_id, message, type))
    conn.commit()
    conn.close()

def get_user_announcements(student_id, limit=10):
    """Get recent announcements for a student."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, message, type, is_read, created_at
        FROM announcements
        WHERE student_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (student_id, limit))
    announcements = cursor.fetchall()
    conn.close()
    return announcements

def mark_announcement_as_read(announcement_id):
    """Mark an announcement as read."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE announcements
        SET is_read = 1
        WHERE id = ?
    """, (announcement_id,))
    conn.commit()
    conn.close()

def create_reservation_log(reservation_id, action, performed_by, notes=None):
    """Create a new reservation log entry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reservation_logs (reservation_id, action, performed_by, notes)
        VALUES (?, ?, ?, ?)
    """, (reservation_id, action, performed_by, notes))
    conn.commit()
    conn.close()

def get_reservation_logs(reservation_id=None):
    """Get reservation logs, optionally filtered by reservation_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if reservation_id:
        cursor.execute("""
            SELECT rl.*, r.student_id, r.laboratory_id, r.computer_no,
                   u.fname || ' ' || u.lastname as performed_by_name
            FROM reservation_logs rl
            JOIN reservations r ON r.id = rl.reservation_id
            JOIN USERS u ON u.idno = rl.performed_by
            WHERE rl.reservation_id = ?
            ORDER BY rl.created_at DESC
        """, (reservation_id,))
    else:
        cursor.execute("""
            SELECT rl.*, r.student_id, r.laboratory_id, r.computer_no,
                   u.fname || ' ' || u.lastname as performed_by_name
            FROM reservation_logs rl
            JOIN reservations r ON r.id = rl.reservation_id
            JOIN USERS u ON u.idno = rl.performed_by
            ORDER BY rl.created_at DESC
            LIMIT 100
        """)
    
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_reservation_by_id(reservation_id):
    """Get a reservation by its ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id,
                student_id,
                laboratory_id,
                computer_no,
                purpose,
                datetime,
                status,
                created_at
            FROM reservations
            WHERE id = ?
        """, (reservation_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'student_id': row[1],
                'laboratory_id': row[2],
                'computer_no': row[3],
                'purpose': row[4],
                'datetime': row[5],
                'status': row[6],
                'created_at': row[7]
            }
        return None
    except Exception as e:
        print(f"Error getting reservation: {e}")
        return None
    finally:
        conn.close()

# Add this at the end of the file
if __name__ == "__main__":
    initialize_database()