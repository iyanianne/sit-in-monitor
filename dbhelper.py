import sqlite3

def add_user(idno, lastname, fname, mname, course, yrlvl, email, username, password):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO USERS (idno, lastname, fname, mname, course, yrlvl, email, username, password) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (idno, lastname, fname, mname, course, yrlvl, email, username, password))
        conn.commit()

def get_user_by_idno_or_username_and_password(idno, username, password):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USERS WHERE idno=? OR username=? AND password=?", (idno, username, password))
        return cursor.fetchone()

def get_admin_by_username_and_password(username, password):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ADMIN WHERE username=? AND password=?", (username, password))
        return cursor.fetchone()

def get_user_by_id(idno):
    with sqlite3.connect("sitinmonitor.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USERS WHERE idno=?", (idno,))
        row = cursor.fetchone()
        if row:
            return {
                "idno": row[0],
                "lastname": row[1],
                "fname": row[2],
                "mname": row[3],
                "course": row[4],
                "yrlvl": row[5],
                "email": row[6],
                "avatar_filename": row[7]
            }
        return None

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
                fname || ' ' || mname || ' ' || lastname AS name, 
                purpose, 
                laboratory 
            FROM USERS
        """)
        
        student = cursor.fetchall()
        return [dict(row) for row in student]  # Convert rows to dictionary

def count_registered_students():
    conn = sqlite3.connect("sitinmonitor.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM USERS")
    result = cursor.fetchone()[0]
    conn.close()
    return result