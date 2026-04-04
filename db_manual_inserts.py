import database as db
from werkzeug.security import generate_password_hash

hashed = generate_password_hash("password")
sql = "INSERT INTO user (fullname, email, role, password) VALUES (?, ?, ?, ?)"
values = ('Super Admin', 'admin@komodohub.com', 'system-admin', hashed)

#Check if this Admin already exists
sql_select = 'SELECT user_id FROM user WHERE fullname = ? AND email = ? AND role = ?'
existing = db.fetch_one(sql_select, (values[0],values[1], values[2]))
if not existing:
    db.execute_query(sql, values)
    print('System admin created successfully')
else: 
    print('System admin by this name already exists, skipping')
