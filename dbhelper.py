import sqlite3

conn = sqlite3.connect('sitinmonitor.db')

cursor = conn.cursor()
cursor.execute('''
               CREATE TABLE USERS (
                idno TEXT PRIMARY KEY,
                lastname TEXT, 
                fname TEXT, 
                mname TEXT, 
                course TEXT, 
                yrlvl TEXT, 
                email TEXT, 
                username TEXT, 
                password TEXT)
               ''')

cursor.execute('''
               CREATE TABLE ADMIN
                username TEXT primary key,
                password TEXT
               ''')

conn.commit()