import sqlite3
from datetime import datetime

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
                fname || ' ' || mname || ' ' || lastname AS name,
                COALESCE(remaining_sessions, 30) as remaining_sessions,
                COALESCE(total_sessions, 30) as total_sessions
            FROM USERS
            WHERE username NOT IN (SELECT username FROM ADMIN)
            ORDER BY lastname, fname
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
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                idno,
                date,
                time_in,
                time_out,
                purpose,
                laboratory
            FROM SIT_IN_HISTORY 
            WHERE idno=?
            ORDER BY date DESC, time_in DESC
        """, (idno,))
        return cursor.fetchall()

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
        
        cursor.execute("""
            UPDATE SIT_IN_HISTORY 
            SET time_out = ?
            WHERE idno = ? AND date = ? AND time_in = time_out
        """, (current_time, idno, current_date))
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
            
            records.append({
                'idno': row[0],
                'name': row[1],
                'date': row[2],
                'time_in': row[3],
                'time_out': row[4],
                'purpose': row[5],
                'laboratory': row[6],
                'course': row[7],
                'year_level': row[8],
                'remaining_sessions': row[9] if row[9] is not None else 30,
                'total_sessions': row[10] if row[10] is not None else 30,
                'duration': duration
            })
        return records