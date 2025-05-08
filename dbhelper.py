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
    try:
        conn = get_db_connection()
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
                COALESCE(total_sessions, 30) as total_sessions,
                COALESCE(lab_points, 0) as lab_points
            FROM USERS 
            WHERE idno = ?
        """, (idno,))
        row = cursor.fetchone()
        
        if row:
            # Return as a tuple for backward compatibility
            return row
        return None
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None
    finally:
        conn.close()

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
    """Get student's remaining and total sessions."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COALESCE(remaining_sessions, 30) as remaining_sessions,
                COALESCE(total_sessions, 30) as total_sessions
            FROM USERS 
            WHERE idno = ?
        """, (idno,))
        result = cursor.fetchone()
        if result:
            return {
                'remaining_sessions': result[0],
                'total_sessions': result[1]
            }
        return {
            'remaining_sessions': 30,
            'total_sessions': 30
        }
    except Exception as e:
        print(f"Error getting student sessions: {e}")
        return {
            'remaining_sessions': 30,
            'total_sessions': 30
        }
    finally:
        conn.close()

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
                h.time_in,
                COALESCE(u.lab_points, 0) as lab_points
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
                'time_in': row[6],
                'lab_points': row[7]
            })
        return students

def end_sit_in_session(idno):
    """End a sit-in session and make the computer available again."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Get the laboratory and computer number from the reservation
        cursor.execute("""
            SELECT r.laboratory_id, r.computer_no
            FROM reservations r
            WHERE r.student_id = ? 
            AND r.status = 'approved'
            ORDER BY r.created_at DESC
            LIMIT 1
        """, (idno,))
        reservation = cursor.fetchone()
        
        # Update the session end time
        cursor.execute("""
            UPDATE SIT_IN_HISTORY 
            SET time_out = ?
            WHERE idno = ? AND date = ? AND time_in = time_out
        """, (current_time, idno, current_date))
        
        # Only decrement if we actually ended a session
        if cursor.rowcount > 0:
            # Make the computer available again
            if reservation:
                cursor.execute("""
                    UPDATE computers 
                    SET is_available = 1 
                    WHERE laboratory_id = ? AND computer_no = ?
                """, (reservation[0], reservation[1]))
            
            cursor.execute("""
                UPDATE USERS 
                SET remaining_sessions = remaining_sessions - 1 
                WHERE idno = ? AND remaining_sessions > 0
            """, (idno,))
        
        conn.commit()
    except Exception as e:
        print(f"Error ending sit-in session: {e}")
    finally:
        conn.close()

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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                u.idno,
                u.lastname || ', ' || u.fname || ' ' || COALESCE(u.mname, '') as name,
                u.course,
                COUNT(DISTINCT h.date || '-' || h.purpose) as sit_in_count,
                COALESCE(u.lab_points, 0) as lab_points
            FROM USERS u
            LEFT JOIN SIT_IN_HISTORY h ON u.idno = h.idno
            WHERE u.username NOT IN (SELECT username FROM ADMIN)
            GROUP BY u.idno, u.lastname, u.fname, u.mname, u.course
            ORDER BY lab_points DESC, sit_in_count DESC
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        leaderboard = []
        for row in results:
            leaderboard.append({
                'idno': str(row[0]),
                'name': str(row[1]),
                'course': str(row[2]),
                'sit_in_count': int(row[3]),
                'lab_points': int(row[4])
            })
        
        # Debug: print the SQL result
        print("LEADERBOARD SQL RESULT:", results)
        
        return leaderboard
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return []
    finally:
        conn.close()

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

def add_lab_points(student_id, points):
    """Add lab points to a student."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First get current points
        cursor.execute("SELECT lab_points FROM USERS WHERE idno = ?", (student_id,))
        current_points = cursor.fetchone()
        
        if current_points is None:
            return False
            
        new_points = (current_points[0] or 0) + points
        
        # Update points
        cursor.execute("""
            UPDATE USERS 
            SET lab_points = ? 
            WHERE idno = ?
        """, (new_points, student_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding lab points: {e}")
        return False
    finally:
        conn.close()

def convert_points_to_session(student_id):
    """Convert 3 points to an additional session."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Get current points and sessions
        cursor.execute("""
            SELECT lab_points, remaining_sessions 
            FROM USERS 
            WHERE idno = ?
        """, (student_id,))
        result = cursor.fetchone()
        
        if not result or result[0] < 3:
            cursor.execute("ROLLBACK")
            return False
            
        current_points = result[0]
        current_sessions = result[1] or 0
        
        # Update points and sessions
        cursor.execute("""
            UPDATE USERS 
            SET lab_points = ?, 
                remaining_sessions = ? 
            WHERE idno = ?
        """, (current_points - 3, current_sessions + 1, student_id))
        
        # Commit transaction
        cursor.execute("COMMIT")
        return True
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"Error converting points to session: {e}")
        return False
    finally:
        conn.close()

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
        
        # Determine if laboratory_id is a lab ID or a lab number 
        # If it's a string that's not a number, it's a lab number
        if isinstance(laboratory_id, str) and not laboratory_id.isdigit():
            # Get the lab ID from the lab number
            cursor.execute("SELECT id FROM laboratories WHERE number = ?", (laboratory_id,))
            lab_result = cursor.fetchone()
            if not lab_result:
                return False, "Laboratory not found"
            laboratory_id = lab_result[0]
        
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
        return False, f"Failed to create reservation: {e}"
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
        
        # Get reservation details first
        cursor.execute("""
            SELECT laboratory_id, computer_no, student_id
            FROM reservations
            WHERE id = ?
        """, (reservation_id,))
        reservation = cursor.fetchone()
        
        if not reservation:
            return False, "Reservation not found"
        
        lab_id = reservation[0]
        computer_no = reservation[1]
        student_id = reservation[2]
        
        # Debug info
        print(f"Approving reservation {reservation_id} for lab_id={lab_id}, computer={computer_no}, student={student_id}")
        
        # Check laboratory name
        cursor.execute("SELECT number FROM laboratories WHERE id = ?", (lab_id,))
        lab_result = cursor.fetchone()
        lab_number = lab_result[0] if lab_result else "Unknown"
        print(f"Laboratory number: {lab_number}")
        
        # Update reservation status to approved
        cursor.execute("""
            UPDATE reservations
            SET status = 'approved'
            WHERE id = ?
        """, (reservation_id,))
        
        # Update computer status to unavailable
        cursor.execute("""
            UPDATE computers
            SET is_available = 0
            WHERE laboratory_id = ? AND computer_no = ?
        """, (lab_id, computer_no))
        
        # Verify the update was successful
        cursor.execute("""
            SELECT is_available FROM computers
            WHERE laboratory_id = ? AND computer_no = ?
        """, (lab_id, computer_no))
        
        computer_status = cursor.fetchone()
        if computer_status:
            print(f"After update, computer {computer_no} in lab {lab_number} has is_available={computer_status[0]}")
        else:
            print(f"Warning: Could not verify status of computer {computer_no} in lab {lab_number}")
        
        # Create a sit-in session for the student
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        cursor.execute("""
            INSERT INTO SIT_IN_HISTORY (idno, date, time_in, time_out, purpose, laboratory)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, current_date, current_time, current_time, "Reservation", f"Laboratory {lab_number}"))
        
        conn.commit()
        return True, "Reservation approved successfully"
    except Exception as e:
        print(f"Error approving reservation: {e}")
        return False, str(e)
    finally:
        conn.close()

def reject_reservation(reservation_id, reason=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update the database schema if the column doesn't exist
        cursor.execute("PRAGMA table_info(reservations)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'rejection_reason' not in column_names:
            cursor.execute("ALTER TABLE reservations ADD COLUMN rejection_reason TEXT")
        
        cursor.execute("""
            UPDATE reservations
            SET status = 'rejected', rejection_reason = ?
            WHERE id = ?
        """, (reason, reservation_id))
        
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
        
        # Get schema info to check available columns
        cursor.execute("PRAGMA table_info(laboratory_status)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Build the query dynamically based on available columns
        select_clause = "SELECT l.id, l.number, COALESCE(s.is_available, 1) as is_available"
        if 'reason' in column_names:
            select_clause += ", s.reason"
        else:
            select_clause += ", NULL as reason"
            
        if 'start_date' in column_names:
            select_clause += ", s.start_date"
        else:
            select_clause += ", NULL as start_date"
            
        if 'end_date' in column_names:
            select_clause += ", s.end_date"
        else:
            select_clause += ", NULL as end_date"
            
        if 'notes' in column_names:
            select_clause += ", s.notes"
        else:
            select_clause += ", NULL as notes"
            
        if 'other_reason' in column_names:
            select_clause += ", s.other_reason"
        else:
            select_clause += ", NULL as other_reason"
        
        # Complete the query
        query = f"""
            {select_clause}
            FROM laboratories l
            LEFT JOIN laboratory_status s ON l.number = s.lab_number
            ORDER BY l.number
        """
        
        cursor.execute(query)
        
        laboratories = []
        for row in cursor.fetchall():
            # Check if lab is scheduled to be unavailable based on date/time
            is_available = bool(row[2])
            start_date = row[4] if len(row) > 4 and row[4] is not None else None
            end_date = row[5] if len(row) > 5 and row[5] is not None else None
            
            # If dates are set and lab is marked unavailable, check if we're in the time range
            if not is_available and start_date and end_date:
                now = datetime.now()
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    
                    # If current time is before start or after end, lab should be available
                    if now < start or now > end:
                        is_available = True
                except Exception as e:
                    print(f"Error parsing dates in get_laboratories: {e}")
            
            laboratories.append({
                'id': row[0],
                'number': row[1],
                'is_available': is_available
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
        
        # Check if laboratory_id is a number (lab id) or a string (lab number)
        lab_id = None
        is_lab_542 = False
        
        if isinstance(laboratory_id, int):
            # It's a lab ID
            lab_id = laboratory_id
            # Check if this is lab 542
            cursor.execute("SELECT number FROM laboratories WHERE id = ?", (laboratory_id,))
            lab_number_result = cursor.fetchone()
            if lab_number_result and lab_number_result[0] == '542':
                is_lab_542 = True
                print(f"PROCESSING LAB 542 (by ID {laboratory_id})")
        else:
            # It's a lab number
            if laboratory_id == '542':
                is_lab_542 = True
                print(f"PROCESSING LAB 542 (by number)")
                
            cursor.execute("""
                SELECT id FROM laboratories WHERE number = ?
            """, (laboratory_id,))
            lab = cursor.fetchone()
            
            if not lab:
                print(f"Laboratory with number {laboratory_id} not found")
                return []
                
            lab_id = lab[0]
            
            # Check if there are any computers for this lab
            cursor.execute("""
                SELECT COUNT(*) FROM computers WHERE laboratory_id = ?
            """, (lab_id,))
            computer_count = cursor.fetchone()[0]
            
            # If no computers exist for this lab, create them
            if computer_count == 0:
                print(f"No computers found for laboratory {laboratory_id}, creating them now")
                # Create 30 computers for this lab
                for i in range(1, 31):
                    cursor.execute("""
                        INSERT INTO computers (laboratory_id, computer_no, is_available)
                        VALUES (?, ?, 1)
                    """, (lab_id, i))
                conn.commit()
        
        # Now get the computers
        cursor.execute("""
            SELECT c.id, c.computer_no, c.is_available
            FROM computers c
            WHERE c.laboratory_id = ?
            ORDER BY c.computer_no
        """, (lab_id,))
        
        computers = []
        rows = cursor.fetchall()
        
        if is_lab_542:
            print(f"LAB 542: Found {len(rows)} computers in database")
            
        for row in rows:
            computer_id = row[0]
            computer_no = row[1]
            is_available = bool(row[2])  # Ensure it's a proper boolean
            
            if is_lab_542:
                print(f"LAB 542 - PC {computer_no}: Status = {'AVAILABLE' if is_available else 'IN USE'} (raw value={row[2]})")
            
            computers.append({
                'id': computer_id,
                'number': computer_no,
                'is_available': is_available
            })
        
        print(f"Returning {len(computers)} computers for laboratory {laboratory_id}")
        return computers
    except Exception as e:
        print(f"Error fetching computers: {e}")
        return []
    finally:
        conn.close()

def update_computer_status(computer_id, is_available, admin_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get computer details first
        cursor.execute("""
            SELECT c.laboratory_id, c.computer_no, c.is_available,
                   COALESCE(r.student_id, '') as student_id
            FROM computers c
            LEFT JOIN reservations r ON 
                r.laboratory_id = c.laboratory_id 
                AND r.computer_no = c.computer_no 
                AND r.status = 'approved'
                AND r.datetime >= date('now')
            WHERE c.id = ?
            ORDER BY r.created_at DESC
            LIMIT 1
        """, (computer_id,))
        computer = cursor.fetchone()
        
        if not computer:
            return False, "Computer not found"
        
        # Update computer status
        cursor.execute("""
            UPDATE computers
            SET is_available = ?
            WHERE id = ?
        """, (1 if is_available else 0, computer_id))
        
        # Log the action
        action = "logged_out" if is_available else "logged_in"
        notes = f"Computer {'made available' if is_available else 'marked as in use'} by admin"
        
        # If there was a student using this computer, log it
        if computer[3]:  # student_id exists
            if is_available:
                # End their sit-in session
                current_date = datetime.now().strftime("%Y-%m-%d")
                current_time = datetime.now().strftime("%H:%M:%S")
                
                cursor.execute("""
                    UPDATE SIT_IN_HISTORY 
                    SET time_out = ?
                    WHERE idno = ? AND date = ? AND time_in = time_out
                """, (current_time, computer[3], current_date))
                
                # Decrement their sessions
                cursor.execute("""
                    UPDATE USERS 
                    SET remaining_sessions = remaining_sessions - 1 
                    WHERE idno = ? AND remaining_sessions > 0
                """, (computer[3],))
                
                notes = f"Admin ended session for student {computer[3]}"
        
        # Log the reservation action
        cursor.execute("""
            INSERT INTO reservation_logs 
            (student_id, laboratory_id, computer_no, action, performed_by, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (computer[3] or 'ADMIN', computer[0], computer[1], action, admin_id, notes))
        
        conn.commit()
        return True, "Computer status updated successfully"
    except Exception as e:
        print(f"Error updating computer status: {e}")
        return False, str(e)
    finally:
        conn.close()

def check_user_has_pending_reservation(student_id):
    """Check if a user has any pending or approved reservations."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM reservations 
            WHERE student_id = ? 
            AND status IN ('pending', 'approved')
            AND datetime >= date('now')
        """, (student_id,))
        
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"Error checking user reservations: {e}")
        return False
    finally:
        conn.close()

def ensure_lab_points_column():
    """Ensure the lab_points column exists in USERS table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if lab_points column exists
        cursor.execute("PRAGMA table_info(USERS)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Add lab_points column if it doesn't exist
        if 'lab_points' not in column_names:
            print("Adding lab_points column to USERS table")
            cursor.execute("ALTER TABLE USERS ADD COLUMN lab_points INTEGER DEFAULT 0")
            conn.commit()
            return True
        return False
    except Exception as e:
        print(f"Error ensuring lab_points column: {e}")
        return False
    finally:
        conn.close()

def ensure_reservation_logs_table():
    """Ensure the reservation_logs table has the correct schema."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reservation_logs'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            # Create the table with the proper schema if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reservation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    laboratory_id INTEGER NOT NULL,
                    computer_no INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    performed_by TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Reservation logs table created successfully")
        else:
            # Check if all required columns exist
            cursor.execute("PRAGMA table_info(reservation_logs)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            # Check for required columns
            required_columns = ['student_id', 'laboratory_id', 'computer_no', 'action', 'performed_by', 'notes', 'created_at']
            missing_columns = [col for col in required_columns if col not in column_names]
            
            # Add any missing columns
            for col in missing_columns:
                data_type = "TEXT"
                if col in ['laboratory_id', 'computer_no']:
                    data_type = "INTEGER"
                elif col == 'created_at':
                    data_type = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    
                cursor.execute(f"ALTER TABLE reservation_logs ADD COLUMN {col} {data_type}")
                print(f"Added missing column {col} to reservation_logs table")
        
        conn.commit()
        print("Reservation logs table schema verified")
        return True
    except Exception as e:
        print(f"Error ensuring reservation_logs table: {e}")
        return False
    finally:
        conn.close()

def initialize_database():
    """Set up the database tables if they don't exist."""
    print("Initializing database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create the users table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idno TEXT UNIQUE,
        lastname TEXT,
        firstname TEXT,
        middlename TEXT,
        course TEXT,
        yrlvl TEXT,
        email TEXT,
        avatar TEXT,
        username TEXT UNIQUE,
        password TEXT,
        remaining_sessions INTEGER DEFAULT 30,
        total_sessions INTEGER DEFAULT 30,
        lab_points INTEGER DEFAULT 0
    )
    """)
    
    # Create admin table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    
    # Create laboratory_status table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS laboratory_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lab_number INTEGER UNIQUE,
        is_available INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_by TEXT
    )
    """)
    
    # Create sit-in table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sit_in (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        purpose TEXT,
        laboratory TEXT,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (student_id) REFERENCES users (idno)
    )
    """)
    
    # Create the laboratory table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS laboratories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT UNIQUE,
        name TEXT,
        capacity INTEGER,
        description TEXT,
        hours TEXT
    )
    """)
    
    # Create the computer table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS computers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        laboratory_id INTEGER,
        computer_no INTEGER,
        is_available BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (laboratory_id) REFERENCES laboratories (id)
    )
    """)
    
    # Create the resources table if it doesn't exist
    cursor.execute("""
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
    """)
    
    # Create the reservations table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        laboratory_id TEXT NOT NULL,
        computer_no INTEGER NOT NULL,
        purpose TEXT NOT NULL,
        datetime TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        rejection_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users(idno)
    )
    """)
    
    # Create the reservation_logs table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_id INTEGER,
        action TEXT NOT NULL,
        performed_by TEXT NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reservation_id) REFERENCES reservations(id)
    )
    """)
    
    # Add a default admin user if none exists
    cursor.execute("SELECT COUNT(*) FROM admin")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ("admin", "admin123"))
    
    # Add default laboratories if none exist
    cursor.execute("SELECT COUNT(*) FROM laboratories")
    count = cursor.fetchone()[0]
    if count == 0:
        labs = [
            ("524", "Programming Laboratory 1", 30, "Main programming lab for CS students", "8:00 AM - 5:00 PM"),
            ("526", "Programming Laboratory 2", 30, "Secondary programming lab", "8:00 AM - 5:00 PM"),
            ("528", "Database Laboratory", 30, "Database and systems lab", "8:00 AM - 5:00 PM"),
            ("530", "Hardware Laboratory", 25, "Computer hardware and networking lab", "8:00 AM - 5:00 PM"),
            ("542", "Multimedia Laboratory", 25, "Graphics and multimedia lab", "8:00 AM - 5:00 PM"),
            ("544", "Special Projects Laboratory", 20, "Research and capstone projects lab", "8:00 AM - 5:00 PM"),
            ("517", "Advanced Programming Laboratory", 30, "Advanced programming and software engineering lab", "8:00 AM - 5:00 PM")
        ]
        
        for lab in labs:
            cursor.execute("""
            INSERT OR IGNORE INTO laboratories (number, name, capacity, description, hours)
            VALUES (?, ?, ?, ?, ?)
            """, lab)
            
            # Get the laboratory ID
            cursor.execute("SELECT id FROM laboratories WHERE number = ?", (lab[0],))
            lab_id = cursor.fetchone()[0]
            
            # Add computers for this laboratory
            for i in range(1, lab[2] + 1):  # Add computers based on capacity
                cursor.execute("""
                INSERT OR IGNORE INTO computers (laboratory_id, computer_no, is_available)
                VALUES (?, ?, ?)
                """, (lab_id, i, True))
    
    # Create settings table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Add resources_enabled setting if it doesn't exist
    cursor.execute("SELECT COUNT(*) FROM settings WHERE key = 'resources_enabled'")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("resources_enabled", "true"))
    
    conn.commit()
    conn.close()
    print("Database initialization complete.")

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

def get_reservation_logs():
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access
        cursor = conn.cursor()
        
        # Get the reservation logs with joined student and lab info
        cursor.execute("""
            SELECT 
                rl.id,
                rl.created_at,
                rl.student_id,
                COALESCE(u.fname || ' ' || u.lastname, rl.student_id) as student_name,
                rl.laboratory_id,
                rl.computer_no,
                rl.action,
                rl.performed_by,
                rl.notes
            FROM reservation_logs rl
            LEFT JOIN USERS u ON rl.student_id = u.idno
            ORDER BY rl.created_at DESC
            LIMIT 1000
        """)
        
        logs = []
        for row in cursor.fetchall():
            # Convert row to dictionary
            log = dict(row)
            
            # Format the timestamp if it exists
            if log.get('created_at'):
                try:
                    # Try to parse the timestamp into a more readable format
                    dt = datetime.strptime(log['created_at'], '%Y-%m-%d %H:%M:%S')
                    log['formatted_date'] = dt.strftime('%b %d, %Y')
                    log['formatted_time'] = dt.strftime('%I:%M %p')
                except Exception as e:
                    print(f"Error formatting timestamp: {e}")
                    log['formatted_date'] = log['created_at']
                    log['formatted_time'] = ''
            
            logs.append(log)
        
        print(f"Retrieved {len(logs)} reservation logs")
        return logs
    except Exception as e:
        print(f"Error getting reservation logs: {e}")
        return []
    finally:
        conn.close()

def log_reservation_action(student_id, laboratory_id, computer_no, action, performed_by, notes=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"Logging reservation action: {action} for student {student_id}, lab {laboratory_id}, computer {computer_no}")
        
        cursor.execute("""
            INSERT INTO reservation_logs 
            (student_id, laboratory_id, computer_no, action, performed_by, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (student_id, laboratory_id, computer_no, action, performed_by, notes))
        
        # Get the ID of the newly inserted log
        log_id = cursor.lastrowid
        print(f"Created reservation log with ID: {log_id}")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error logging reservation action: {e}")
        return False
    finally:
        conn.close()

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

def reset_all_points():
    """Reset all students' lab points to 0."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE USERS 
            SET lab_points = 0 
            WHERE username NOT IN (SELECT username FROM ADMIN)
        """)
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error resetting points: {e}")
        return False
    finally:
        conn.close()

def get_user_reservations(student_id):
    """Get reservation history for a specific student."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if rejection_reason column exists
        cursor.execute("PRAGMA table_info(reservations)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Set up the query based on whether the rejection_reason column exists
        if 'rejection_reason' in column_names:
            query = """
                SELECT 
                    r.id,
                    r.laboratory_id,
                    r.computer_no,
                    r.purpose,
                    r.datetime,
                    r.status,
                    r.created_at,
                    r.rejection_reason
                FROM reservations r
                WHERE r.student_id = ?
                ORDER BY r.created_at DESC
            """
        else:
            query = """
                SELECT 
                    r.id,
                    r.laboratory_id,
                    r.computer_no,
                    r.purpose,
                    r.datetime,
                    r.status,
                    r.created_at
                FROM reservations r
                WHERE r.student_id = ?
                ORDER BY r.created_at DESC
            """
        
        cursor.execute(query, (student_id,))
        
        reservations = []
        for row in cursor.fetchall():
            reservation = {
                'id': row[0],
                'laboratory': f"Laboratory {row[1]}",
                'computer_no': row[2],
                'purpose': row[3],
                'datetime': row[4],
                'status': row[5],
                'created_at': row[6]
            }
            
            # Add rejection_reason if available
            if 'rejection_reason' in column_names and len(row) > 7:
                reservation['rejection_reason'] = row[7]
            
            reservations.append(reservation)
        
        return reservations
    except Exception as e:
        print(f"Error fetching user reservations: {e}")
        return []
    finally:
        conn.close()

# Resource management functions
def get_all_resources():
    """Get all uploaded resources."""
    conn = sqlite3.connect("sitinmonitor.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Create table if it doesn't exist
        cursor.execute("""
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
        """)
        conn.commit()
        
        cursor.execute("""
            SELECT id, title, description, category, file_path, original_filename, 
                file_type, file_size, uploaded_by, strftime('%Y-%m-%d %H:%M', created_at) as upload_date 
            FROM resources 
            ORDER BY created_at DESC
        """)
        
        resources = cursor.fetchall()
        return resources
    except Exception as e:
        print(f"Error getting resources: {e}")
        return []
    finally:
        conn.close()

def get_resources_by_category(category):
    """Get resources filtered by category."""
    conn = sqlite3.connect("sitinmonitor.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Create table if it doesn't exist
        cursor.execute("""
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
        """)
        conn.commit()
        
        cursor.execute("""
            SELECT id, title, description, category, file_path, original_filename, 
                file_type, file_size, uploaded_by, strftime('%Y-%m-%d %H:%M', created_at) as upload_date 
            FROM resources 
            WHERE category = ?
            ORDER BY created_at DESC
        """, (category,))
        
        resources = cursor.fetchall()
        return resources
    except Exception as e:
        print(f"Error getting resources by category: {e}")
        return []
    finally:
        conn.close()

def get_resource_by_id(resource_id):
    """Get resource by its ID."""
    conn = sqlite3.connect("sitinmonitor.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, title, description, category, file_path, original_filename, 
                file_type, file_size, uploaded_by, strftime('%Y-%m-%d %H:%M', created_at) as upload_date 
            FROM resources 
            WHERE id = ?
        """, (resource_id,))
        
        resource = cursor.fetchone()
        return resource
    except Exception as e:
        print(f"Error getting resource by ID: {e}")
        return None
    finally:
        conn.close()

def add_resource(title, description, category, file_path, original_filename, file_type, file_size, uploaded_by):
    """Add a new resource to the database."""
    conn = sqlite3.connect("sitinmonitor.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
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
        """)
        
        cursor.execute("""
            INSERT INTO resources (title, description, category, file_path, original_filename, file_type, file_size, uploaded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, description, category, file_path, original_filename, file_type, file_size, uploaded_by))
        
        conn.commit()
        resource_id = cursor.lastrowid
        return resource_id
    except Exception as e:
        print(f"Error adding resource: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def delete_resource(resource_id):
    """Delete a resource from the database."""
    conn = sqlite3.connect("sitinmonitor.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
        conn.commit()
        success = cursor.rowcount > 0
        return success
    except Exception as e:
        print(f"Error deleting resource: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_lab_status(lab_number, is_available, admin_username):
    """Update the availability status of a laboratory."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if the lab already has a status
        cursor.execute("SELECT id FROM laboratory_status WHERE lab_number = ?", (lab_number,))
        result = cursor.fetchone()
        
        if result:
            # Update existing status
            cursor.execute("""
                UPDATE laboratory_status
                SET is_available = ?, updated_at = datetime('now', 'localtime'), updated_by = ?
                WHERE lab_number = ?
            """, (1 if is_available else 0, admin_username, lab_number))
        else:
            # Insert new status
            cursor.execute("""
                INSERT INTO laboratory_status (lab_number, is_available, updated_by)
                VALUES (?, ?, ?)
            """, (lab_number, 1 if is_available else 0, admin_username))
        
        conn.commit()
        return True, "Laboratory status updated successfully"
    except Exception as e:
        print(f"Error updating laboratory status: {e}")
        return False, str(e)
    finally:
        conn.close()

def get_lab_statuses():
    """Get the status of all laboratories."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if required columns exist
        cursor.execute("PRAGMA table_info(laboratory_status)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Build the query dynamically based on available columns
        select_clause = "SELECT lab_number, is_available, updated_at, updated_by"
        
        # Add optional columns if they exist
        for col in ['reason', 'start_date', 'end_date', 'notes', 'other_reason']:
            if col in column_names:
                select_clause += f", {col}"
            else:
                select_clause += f", NULL as {col}"
                
                # Try to add the missing column
                try:
                    cursor.execute(f"ALTER TABLE laboratory_status ADD COLUMN {col} TEXT")
                    print(f"Added missing column {col} to laboratory_status table")
                except Exception as e:
                    if "duplicate column name" not in str(e):
                        print(f"Error adding column {col}: {e}")
        
        # Complete the query
        query = f"""
            {select_clause}
            FROM laboratory_status
            ORDER BY lab_number
        """
        
        cursor.execute(query)
        
        statuses = []
        for row in cursor.fetchall():
            # Get the column indices based on the query we built
            lab_number_idx = 0
            is_available_idx = 1
            updated_at_idx = 2
            updated_by_idx = 3
            reason_idx = 4
            start_date_idx = 5
            end_date_idx = 6
            notes_idx = 7
            other_reason_idx = 8
            
            # Get values safely
            lab_number = row[lab_number_idx]
            is_available = bool(row[is_available_idx]) if row[is_available_idx] is not None else True
            updated_at = row[updated_at_idx]
            updated_by = row[updated_by_idx]
            reason = row[reason_idx] if len(row) > reason_idx else None
            start_date = row[start_date_idx] if len(row) > start_date_idx else None
            end_date = row[end_date_idx] if len(row) > end_date_idx else None
            notes = row[notes_idx] if len(row) > notes_idx else None
            other_reason = row[other_reason_idx] if len(row) > other_reason_idx else None
            
            # Check if lab is scheduled to be unavailable based on date/time
            if not is_available and start_date and end_date:
                now = datetime.now()
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    
                    # If current time is before start or after end, lab should be available
                    if now < start or now > end:
                        is_available = True
                except Exception as e:
                    print(f"Error parsing dates: {e}")
            
            statuses.append({
                'labNumber': lab_number,
                'available': is_available,
                'updatedAt': updated_at,
                'updatedBy': updated_by,
                'reason': reason or '',
                'startDate': start_date or '',
                'endDate': end_date or '',
                'notes': notes or '',
                'otherReason': other_reason or ''
            })
        
        return statuses
    except Exception as e:
        print(f"Error fetching laboratory statuses: {e}")
        return []
    finally:
        conn.close()

def update_lab_schedule(lab_number, is_available, admin_username, reason='', start_date='', end_date='', notes='', other_reason=''):
    """Update the laboratory schedule with detailed information."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if we need to update or create the table first
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS laboratory_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lab_number TEXT NOT NULL,
                is_available INTEGER NOT NULL DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT NOT NULL
            )
        """)
        
        # Add any missing columns that might not exist in older versions
        columns_to_check = [
            ('reason', 'TEXT'),
            ('start_date', 'TEXT'),
            ('end_date', 'TEXT'),
            ('notes', 'TEXT'),
            ('other_reason', 'TEXT')
        ]
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(laboratory_status)")
        column_names = [column[1] for column in cursor.fetchall()]
        
        # Add missing columns
        for column_name, column_type in columns_to_check:
            if column_name not in column_names:
                try:
                    cursor.execute(f"ALTER TABLE laboratory_status ADD COLUMN {column_name} {column_type}")
                    print(f"Added column {column_name} to laboratory_status table")
                except Exception as e:
                    print(f"Error adding column {column_name}: {e}")
        
        # Check if the lab already has a status
        cursor.execute("SELECT id FROM laboratory_status WHERE lab_number = ?", (lab_number,))
        result = cursor.fetchone()
        
        if result:
            # Update existing status
            cursor.execute("""
                UPDATE laboratory_status
                SET is_available = ?, 
                    updated_at = datetime('now', 'localtime'), 
                    updated_by = ?,
                    reason = ?,
                    start_date = ?,
                    end_date = ?,
                    notes = ?,
                    other_reason = ?
                WHERE lab_number = ?
            """, (
                1 if is_available else 0, 
                admin_username, 
                reason,
                start_date, 
                end_date,
                notes,
                other_reason,
                lab_number
            ))
        else:
            # Insert new status
            cursor.execute("""
                INSERT INTO laboratory_status 
                (lab_number, is_available, updated_by, reason, start_date, end_date, notes, other_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lab_number, 
                1 if is_available else 0, 
                admin_username,
                reason,
                start_date, 
                end_date,
                notes,
                other_reason
            ))
        
        conn.commit()
        return True, "Laboratory schedule updated successfully"
    except Exception as e:
        print(f"Error updating laboratory schedule: {e}")
        return False, str(e)
    finally:
        conn.close()

def refresh_lab_schedules():
    """Check all scheduled lab unavailability and update status if needed"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if required columns exist
        cursor.execute("PRAGMA table_info(laboratory_status)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # If required columns don't exist, just return
        required_columns = ['is_available', 'start_date', 'end_date']
        if not all(col in column_names for col in required_columns):
            print("Missing required columns for lab schedule refresh")
            # Try to add them
            for col in ['start_date', 'end_date']:
                if col not in column_names:
                    try:
                        cursor.execute(f"ALTER TABLE laboratory_status ADD COLUMN {col} TEXT")
                        print(f"Added missing column {col} to laboratory_status table")
                    except Exception as e:
                        print(f"Error adding column {col}: {e}")
            conn.commit()
            return False
        
        # Get all labs with scheduled unavailability
        cursor.execute("""
            SELECT lab_number, is_available, start_date, end_date
            FROM laboratory_status
            WHERE is_available = 0 
              AND (start_date IS NOT NULL AND start_date != '')
              AND (end_date IS NOT NULL AND end_date != '')
        """)
        
        now = datetime.now()
        for row in cursor.fetchall():
            lab_number = row[0]
            start_date = row[2]
            end_date = row[3]
            
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                # Check if we need to update the lab status
                if now < start or now > end:
                    # The scheduled unavailability is not currently active
                    # Update the database to show as available
                    print(f"Auto-enabling lab {lab_number} as schedule is not active")
                    cursor.execute("""
                        UPDATE laboratory_status
                        SET is_available = 1, 
                            updated_at = datetime('now', 'localtime'),
                            updated_by = 'SYSTEM'
                        WHERE lab_number = ?
                    """, (lab_number,))
            except Exception as e:
                print(f"Error checking dates for lab {lab_number}: {e}")
        
        # Also check for labs that should now be unavailable
        cursor.execute("""
            SELECT lab_number, is_available, start_date, end_date
            FROM laboratory_status
            WHERE is_available = 1 
              AND (start_date IS NOT NULL AND start_date != '')
              AND (end_date IS NOT NULL AND end_date != '')
        """)
        
        for row in cursor.fetchall():
            lab_number = row[0]
            start_date = row[2]
            end_date = row[3]
            
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                # Check if we need to update the lab status
                if start <= now <= end:
                    # The scheduled unavailability is currently active
                    # Update the database to show as unavailable
                    print(f"Auto-disabling lab {lab_number} as schedule is now active")
                    cursor.execute("""
                        UPDATE laboratory_status
                        SET is_available = 0, 
                            updated_at = datetime('now', 'localtime'),
                            updated_by = 'SYSTEM'
                        WHERE lab_number = ?
                    """, (lab_number,))
            except Exception as e:
                print(f"Error checking dates for lab {lab_number}: {e}")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error refreshing lab schedules: {e}")
        return False
    finally:
        conn.close()

# Add this at the end of the file
if __name__ == "__main__":
    initialize_database()