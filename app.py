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

#Fetching organizatiions for registration dropdown
@app.route('/get-organizations', methods=['GET'])
def get_organizations():
    category = request.args.get('category') # 'school' or 'community'
    sql = 'SELECT organization_id, name  FROM organization WHERE category = ?'
    orgs = db.fetch_query(sql, (category,))
    return jsonify({'success': True, 'organizations': [dict(o) for o in orgs]})

#Verify registration for teacher / principal / community-member
@app.route('/verify-registration', methods=['POST'])
def verify_registration():
    data = request.get_json()
    email = data.get('email')
    org_id = data.get('organization_id')
    role = data.get('role')
    
    sql = 'SELECT id FROM registration WHERE email = ? AND organization_id = ? AND role = ? AND status = ?'
    values = (email, org_id, role, 'pending')
    record = db.fetch_one(sql, values)
    
    if not record:
        return jsonify({'success': False, 'message': f'No pending registration found for this email: {email}'})
    
    sql = 'UPDATE registration SET status = ? WHERE email = ? AND organization_id = ?'
    db.execute_query(sql, ('registered', email, org_id))
    
    return jsonify ({'success': True})


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
    org_id = data.get('orgId')
    
    needs_code = ['student',]
    needs_org = ['school-admin', 'community-admin']
    
    # Verify registration for student
    if role in needs_code:
        sql = 'SELECT id, organization_id FROM registration WHERE email = ? AND access_code = ? AND status = ?'
        values = (email, access_code, 'pending')    
        record = db.fetch_one(sql, values)
        if not record:
            return jsonify({'success': False, 'message': 'Invalid or already used access code'})
        org_id = record['organization_id']
     
    # Check email not already registered   
    sql = 'SELECT user_id FROM user WHERE email = ?'
    existing = db.fetch_one(sql, (email, ))
    if existing:
        return jsonify({'success': False, 'message': 'An account with this email already exists.'})
    
    # Create user
    hashed = generate_password_hash(password)
    sql = 'INSERT INTO user (fullname, email, role, password, organization_id) VALUES (?, ?, ?, ?, ?)'
    values = (name, email, role, hashed, org_id)
    db.execute_query(sql, values)
    
    # Mark access code as used
    if role in needs_code:
        sql = 'UPDATE registration SET status = ? WHERE email = ?'
        values = ('registered', email,)
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
    session['organization_id'] = user['organization_id']
    
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

#Get activities page
@app.route('/activities')
def get_activities():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'], ))
    return render_template('shared/activity.html', user = user)

#Get Creatinv Canvas page
@app.route('/creative-canvas')
def get_creative_canvas():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'], ))
    return render_template('shared/creative-canvas.html', user = user)

# Get Massages
@app.route('/messages')
def get_messages():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'], ))
    return render_template('shared/messages.html', user = user)

#Get my profile details
@app.route('/my-profile')
def get_my_profile():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'], ))
    return render_template('shared/my-profile.html', user = user)

#Sighting Reporting form handling
@app.route('/report-sighting')
def report_sighting():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    sql = 'SELECT * FROM user WHERE user_id = ?'
    user = db.fetch_one(sql, (session['user_id'],))
    sql = 'SELECT species_id, common_name FROM species'
    species = db.fetch_query(sql)
    return render_template('shared/report-sighting-form.html', user=user, species=species)

#Get Sighting Reports
@app.route('/sighting-reports')
def get_sighting_reports():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'], ))
    return render_template('shared/sighting-reports-view.html', user = user)

#Handle Registering students / teacher / community members by Admins
@app.route('/register-member')
def get_member_registration_form():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ? ', (session['user_id'],))
    return render_template('shared/register-member.html', user = user)

#Handling Member Registration
@app.route('/register-member', methods = ['POST'])
def register_member():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    data = request.get_json()
    role = data.get('role')
    full_name = data.get('fullName')
    email = data.get('email')
    accessCode = data.get('accessCode')
    org_id = session.get('organization_id') #Geting admin's org_id from session
    
    #Checking if email already registered in registration table
    existing = db.fetch_one('SELECT id FROM registration WHERE email = ?', (email, ))
    if existing:
        return jsonify({'success': False, 'message': 'This email is already registered'})
    
    #Insert into registeration table
    sql = 'INSERT INTO registration (email, full_name, role, access_code, organization_id) VALUES (?, ?, ?, ?, ?)'
    db.execute_query(sql, (email, full_name, role, accessCode, org_id))
    
    return jsonify({'success': True})
    
#Retrieving Teachers Details for School admin
@app.route('/manage-teachers')
def get_teachers_details():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'], ))
    return render_template('shared/manage-users.html', user=user)

#Retrieving Students Details for School admin
@app.route('/manage-students')
def get_students_details():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'], ))
    return render_template('shared/manage-users.html', user=user)

#Retrieving Community members details for community admin
@app.route('/manage-members')
def get_members_details():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'], ))
    return render_template('shared/manage-users.html', user=user)

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