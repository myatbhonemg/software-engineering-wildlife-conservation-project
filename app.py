#Importing required libraries
from flask import (
    Flask, 
    url_for, 
    render_template, 
    request, 
    redirect, 
    abort, 
    flash,
    session,
    jsonify,
    send_file
    )
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import database as db
import os 
from werkzeug.utils import secure_filename
import time


#Initializing the app
app = Flask(__name__)

app.secret_key = 'secret-key'

#Handling the route to home page
@app.route('/home')
def home():
    sql = 'SELECT * FROM species'
    species = db.fetch_query(sql)
    return render_template("home.html", species = species)

#Redirecting to home page if no path provided
@app.route('/')
def home1():
    return redirect(url_for('home'))

#Handling file uploads and extensions
UPLOAD_FOLDER = 'static/uploads/sightings'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#=====REGISTRATION PROCESS===== 
#Handling access code request request
@app.route("/access-code-request", methods = ['POST'])
def access_code_request_handle():
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')
    
    sql = "SELECT access_code FROM registration WHERE email = ? AND role = ? AND status = ?"
    values = (email, role, 'pending')
    record = db.fetch_one(sql, values)
    
    if not record:
        return jsonify({'success': False, 'message': 'No pending registration found for this email'})

    return jsonify ({'success': True, 'accessCode': record['access_code'] })

#Registering account final step
@app.route('/register-account', methods=['POST'])
def account_registration():
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')
    name = data.get('name')
    password = data.get('password')
    access_code = data.get('accessCodeParam')
    org_data = data.get('orgData')
    
    needs_code = ['student', 'teacher']
    needs_org = ['school-admin', 'community-admin']
    
    # Verify access code for student / teacher
    if role in needs_code:
        sql = 'SELECT id FROM registration WHERE email = ? AND access_code = ? AND status = ?'
        values = (email, access_code, 'pending')    
        record = db.fetch_one(sql, values)
        if not record:
            return jsonify({'success': False, 'message': 'Invalid or already used access code'})
     
    # Check email not already registered   
    sql = 'SELECT user_id FROM user WHERE email = ?'
    existing = db.fetch_one(sql, (email, ))
    if existing:
        return jsonify({'success': False, 'message': 'An account with this email already exists.'})
    
    # Create user
    hashed = generate_password_hash(password)
    sql = 'INSERT INTO user (fullname, email, role, password) VALUES (?, ?, ?, ?)'
    values = (name, email, role, hashed)
    db.execute_query(sql, values)
    
    # Mark access code as used
    if role in needs_code:
        sql = 'UPDATE registration SET status = ? WHERE id = ?'
        values = ('registered', record['id'],)
        db.execute_query(sql, values)
    
    # Create org record for school-admin or community-admin
    if role in needs_org and org_data:
        category = 'school' if role == 'school-admin' else 'community'
        sql = "INSERT INTO organization (name, category, type, email, address) VALUES (?, ?, ?, ?, ?)"
        values = (org_data['name'],category, org_data['type'], org_data['email'], org_data['address'])
        db.execute_query(sql, values)
        
        # Get org_id just inserted
        sql = "SELECT organization_id FROM organization WHERE email = ?"
        org = db.fetch_one(sql, (org_data['email'],))
        org_id = org['organization_id']
        
        # Update user table with org_id
        sql = "UPDATE user SET organization_id = ? WHERE email = ?"
        db.execute_query(sql, (org_id, email))
    
    return jsonify({'success': True})


#=====LOGIN PROCESS====
@app.route('/login', methods=['GET'])
def login_get():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Find user by email
    sql = 'SELECT * FROM user WHERE email = ?'
    user = db.fetch_one(sql, (email, ))
    
    #Check if user exists
    if not user:
        return jsonify({'success': False, 'message': 'No account found with this email'})
    
    # Check password
    if not check_password_hash(user['password'], password):
        return jsonify({'success': False, 'message': 'Incorrect password'})
    
    #Saving user to session after successfull login
    session['user_id'] = user['user_id']
    session['role'] = user['role']
    session['fullname'] = user['fullname']
    session['email'] = user['email']
    
    # Map role to dashboard
    role_redirects = {
        'student': '/dashboard/student',         
        'teacher': '/dashboard/teacher',
        'school-admin': '/dashboard/school-admin',
        'system-admin': '/dashboard/system-admin',
        'community-member': '/dashboard/community-member',
        'community-admin': '/dashboard/community-admin',
        'principal': '/dashboard/principal',
        'public': '/dashboard/public'
    }
    
    redirect_url = role_redirects.get(user['role'], '/')
    
    return jsonify({
        'success': True,
        'fullname': user['fullname'],
        'role': user['role'],
        'redirectTo': redirect_url
    })

# ===== Logout route =====
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_get'))
  
# ======= DASHBOARDS ========
#Retriving students data from DB and filling its dashboard   
@app.route('/dashboard/student')
def student_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    sql = "SELECT * FROM user WHERE user_id = ?"
    user = db.fetch_one(sql, (session['user_id'], ))
    return render_template('student-dashboard.html', user = user)

#Retriving teacher's data from DB and filling its dashboard
@app.route('/dashboard/teacher')
def teacher_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    return render_template('teacher-dashboard.html', user=user)

#Retriving school admin's  data from DB and filling its dashboard
@app.route('/dashboard/school-admin')
def school_admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    return render_template('school-admin-dashboard.html', user=user)

#Retriving school principal's  data from DB and filling its dashboard
@app.route('/dashboard/principal')
def principal_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    return render_template('principal-dashboard.html', user=user)

#Retriving system admin's  data from DB and filling its dashboard        
@app.route('/dashboard/system-admin')
def system_admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    return render_template('system-admin-dashboard.html', user=user)
         
#Retriving community member's  data from DB and filling its dashboard        
@app.route('/dashboard/community-member')
def community_member_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    return render_template('community-dashboard.html', user=user)

#Retriving community admin's  data from DB and filling its dashboard        
@app.route('/dashboard/community-admin')
def community_admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    return render_template('community-admin-dashboard.html', user=user)
    
#Retriving public user's  data from DB and filling its dashboard        
@app.route('/dashboard/public')
def public_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    return render_template('public-dashboard.html', user=user)


#Retrieving species data to fill species library page
@app.route('/species-library')
def species_library():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ? ', (session['user_id'],))
    sql = 'SELECT * FROM species'
    species = db.fetch_query(sql)
    return render_template("shared/species-library.html", user = user, species = species)

#Sighting Reporting form handling
@app.route('/report-sighting')
def report_sighting():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    sql = 'SELECT * FROM user WHERE user_id = ?'
    user = db.fetch_one(sql, (session['user_id'],))
    sql = 'SELECT species_id, common_name FROM species'
    species = db.fetch_query(sql)
    return render_template('shared/report-sighting.html', user=user, species=species)

#Handling Sighting Reports submission
@app.route('/submit-sighting', methods=['POST'])
def submit_sighting():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    photo_path = None
    if 'photos' in request.files:
        photo = request.files.getlist('photos')[0]
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            unique_filename = f"{session['user_id']}_{int(time.time())}_{filename}"
            save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            photo.save(save_path)
            photo_path = f"uploads/sightings/{unique_filename}"
            
    
    sql = '''INSERT INTO sighting 
        (species_id, count, location, region, sighting_date, sighting_time, description, condition, photo, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    values = (
        request.form.get('species_id'),
        request.form.get('count'),
        request.form.get('location'),
        request.form.get('region'),
        request.form.get('date'),
        request.form.get('time'),
        request.form.get('description'),
        request.form.get('condition'),
        photo_path,
        session['user_id']
    )    
    db.execute_query(sql, values)
    return jsonify({'success': True})



if __name__ == '__main__':
    app.run(
        debug=True,
        host = '0.0.0.0',
        port = 5000
    )