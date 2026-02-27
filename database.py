import sqlite3

#Initializing database by running Database_schema.sql
def init_db():
    with sqlite3.connect('Komodo_DB.db') as con:
        with open('Database_schema.sql', 'r') as f:
            con.executescript(f.read())
            print("Database was created successfully")
            
    
#For INSERT, UPDATE, DELETE queries
def execute_query(sql, params=()):
    with sqlite3.connect('Komodo_DB.db') as con:
        cur = con.cursor()
        cur.execute(sql, params)
        con.commit()
        row_count = cur.rowcount
        return row_count

#For SELECT * queries  
def fetch_query(sql, params=()):
    with sqlite3.connect('Komodo_DB.db') as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        return rows
    
#For SELECT queries returning single row
def fetch_one(sql, params=()):
    with sqlite3.connect('Komodo_DB.db') as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        return row


#Run this file once directly from terminal to creat database and tables
if __name__ == '__main__':
    init_db()    