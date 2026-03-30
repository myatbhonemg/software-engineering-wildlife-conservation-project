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
from datetime import datetime, timedelta
import re

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

#Handling file uploads folders and extensions
UPLOAD_FOLDER = 'static/uploads/sightings'
AVATAR_FOLDER = 'static/uploads/avatars'
MESSAGE_ATTACHMENT_FOLDER = 'static/uploads/message-attachments'
PROGRAM_FILES_FOLDER = 'static/uploads/program-files'
CHALLENGE_MEDIA_FOLDER = 'static/uploads/challenge-media'


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
    sql = 'INSERT INTO user (fullname, email, role, password, organization_id, created_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)'
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
    org_id = session.get('organization_id')

    teachers = db.fetch_one(
        "SELECT COUNT(*) as count FROM user WHERE role = 'teacher' AND organization_id = ?",
        (org_id,)
    )
    students = db.fetch_one(
        "SELECT COUNT(*) as count FROM user WHERE role = 'student' AND organization_id = ?",
        (org_id,)
    )
    sightings = db.fetch_one(
        '''SELECT COUNT(*) as count FROM sighting s
           JOIN user u ON s.user_id = u.user_id
           WHERE u.organization_id = ?''',
        (org_id,)
    )
    classes = db.fetch_one(
        "SELECT COUNT(*) as count FROM class WHERE organization_id = ?",
        (org_id,)
    )
    pending_staff = db.fetch_one(
        '''SELECT COUNT(*) as count FROM registration
           WHERE organization_id = ? AND role IN ('teacher', 'principal') AND status = 'pending' ''',
        (org_id,)
    )
    pending_students = db.fetch_one(
        '''SELECT COUNT(*) as count FROM registration
           WHERE organization_id = ? AND role = 'student' AND status = 'pending' ''',
        (org_id,)
    )

    return render_template('school-admin-dashboard.html',
        user=user,
        teacher_count=teachers['count'],
        student_count=students['count'],
        sighting_count=sightings['count'],
        class_count=classes['count'],
        pending_staff=pending_staff['count'],
        pending_students=pending_students['count']
    )
    
#Retriving school principal's  data from DB and filling its dashboard
@app.route('/dashboard/principal')
def principal_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    org_id = session.get('organization_id')

    teachers = db.fetch_one(
        "SELECT COUNT(*) as count FROM user WHERE role = 'teacher' AND organization_id = ?",
        (org_id,)
    )
    students = db.fetch_one(
        "SELECT COUNT(*) as count FROM user WHERE role = 'student' AND organization_id = ?",
        (org_id,)
    )
    sightings = db.fetch_one(
        '''SELECT COUNT(*) as count FROM sighting s
           JOIN user u ON s.user_id = u.user_id
           WHERE u.organization_id = ?''',
        (org_id,)
    )
    classes = db.fetch_one(
        "SELECT COUNT(*) as count FROM class WHERE organization_id = ?",
        (org_id,)
    )
    pending_staff = db.fetch_one(
        '''SELECT COUNT(*) as count FROM registration 
           WHERE organization_id = ? AND role IN ('teacher', 'principal') AND status = 'pending' ''',
        (org_id,)
    )
    pending_students = db.fetch_one(
        '''SELECT COUNT(*) as count FROM registration 
           WHERE organization_id = ? AND role = 'student' AND status = 'pending' ''',
        (org_id,)
    )

    return render_template('principal-dashboard.html',
        user=user,
        teacher_count=teachers['count'],
        student_count=students['count'],
        sighting_count=sightings['count'],
        class_count=classes['count'],
        pending_staff=pending_staff['count'],
        pending_students=pending_students['count']
    )
    
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
    org_id = session.get('organization_id')

    members = db.fetch_one(
        "SELECT COUNT(*) as count FROM user WHERE role = 'community-member' AND organization_id = ?",
        (org_id,)
    )
    sightings = db.fetch_one(
        '''SELECT COUNT(*) as count FROM sighting s
           JOIN user u ON s.user_id = u.user_id
           WHERE u.organization_id = ?''',
        (org_id,)
    )
    active_challenges = db.fetch_one(
        '''SELECT COUNT(*) as count FROM challenge
           WHERE organization_id = ? AND deadline > ?''',
        (org_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    pending_members = db.fetch_one(
        '''SELECT COUNT(*) as count FROM registration
           WHERE organization_id = ? AND role = 'community-member' AND status = 'pending' ''',
        (org_id,)
    )

    return render_template('community-admin-dashboard.html',
        user=user,
        member_count=members['count'],
        sighting_count=sightings['count'],
        active_challenges=active_challenges['count'],
        pending_members=pending_members['count']
    )
    
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
    
    #Fetching all species info
    sql = 'SELECT * FROM species'
    species = db.fetch_query(sql)
    
    #Fetching all sightings with reporter and species info
    sql = '''SELECT s.sighting_id, s.count, s.location, s.region,
        s.sighting_date, s.description, s.photo,
        sp.common_name,
        u.fullname as reporter_name, u.role as reporter_role,
        u.avatar as reporter_avatar, u.organization_id as reporter_org_id
        FROM sighting s
        JOIN species sp ON s.species_id = sp.species_id
        JOIN user u ON s.user_id = u.user_id
        ORDER BY s.submitted_at DESC'''
    sightings = db.fetch_query(sql)
    
    return render_template("shared/species-library.html", user = user, species = species, sightings = sightings)

# ===== CLASSES =====
# Getting classes details
@app.route('/classes')
def get_classes():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] not in ['school-admin', 'principal']:
        return abort(403)

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    org_id = session.get('organization_id')

    # Fetch all classes with teacher name and student count
    sql = '''
        SELECT c.*,
               u.fullname as teacher_name,
               (SELECT COUNT(*) FROM class_enrollment ce WHERE ce.class_id = c.class_id) as student_count
        FROM class c
        LEFT JOIN user u ON c.teacher_id = u.user_id
        WHERE c.organization_id = ?
        ORDER BY c.created_at DESC
    '''
    classes = db.fetch_query(sql, (org_id,))

    # Fetch teachers for the assign dropdown
    teachers = db.fetch_query(
        "SELECT user_id, fullname FROM user WHERE role = 'teacher' AND organization_id = ?",
        (org_id,)
    )

    return render_template('shared/classes.html',
        user=user,
        classes=[dict(c) for c in classes],
        teachers=teachers
    )
    
# Create a class
@app.route('/create-class', methods=['POST'])
def create_class():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data = request.get_json()
    name = data.get('name', '').strip()
    subject = data.get('subject', '').strip()
    teacher_id = data.get('teacher_id')

    if not name:
        return jsonify({'success': False, 'message': 'Class name is required'})

    db.execute_query(
        'INSERT INTO class (name, subject, organization_id, teacher_id) VALUES (?, ?, ?, ?)',
        (name, subject, session['organization_id'], teacher_id or None)
    )

    new_class = db.fetch_one(
        'SELECT class_id FROM class WHERE organization_id = ? ORDER BY created_at DESC LIMIT 1',
        (session['organization_id'],)
    )
    return jsonify({'success': True, 'class_id': new_class['class_id']})
    
# Delete a class
@app.route('/delete-class/<int:class_id>', methods=['POST'])
def delete_class(class_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    cls = db.fetch_one(
        'SELECT * FROM class WHERE class_id = ? AND organization_id = ?',
        (class_id, session['organization_id'])
    )
    if not cls:
        return jsonify({'success': False, 'message': 'Class not found'})

    db.execute_query('DELETE FROM class_enrollment WHERE class_id = ?', (class_id,))
    db.execute_query('DELETE FROM program_class WHERE class_id = ?', (class_id,))
    db.execute_query('DELETE FROM challenge_class WHERE class_id = ?', (class_id,))
    db.execute_query('DELETE FROM class WHERE class_id = ?', (class_id,))

    return jsonify({'success': True})

# Update class teacher
@app.route('/update-class-teacher/<int:class_id>', methods=['POST'])
def update_class_teacher(class_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data = request.get_json()
    teacher_id = data.get('teacher_id')

    db.execute_query(
        'UPDATE class SET teacher_id = ? WHERE class_id = ? AND organization_id = ?',
        (teacher_id or None, class_id, session['organization_id'])
    )
    return jsonify({'success': True})

# Get students in a class
@app.route('/get-class-students/<int:class_id>')
def get_class_students(class_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    # Students in the class
    enrolled = db.fetch_query(
        '''SELECT u.user_id, u.fullname, u.email, u.avatar
           FROM class_enrollment ce
           JOIN user u ON ce.student_id = u.user_id
           WHERE ce.class_id = ?
           ORDER BY u.fullname''',
        (class_id,)
    )

    # Students in the org NOT in this class
    available = db.fetch_query(
        '''SELECT u.user_id, u.fullname, u.email, u.avatar
           FROM user u
           WHERE u.role = 'student'
           AND u.organization_id = ?
           AND u.user_id NOT IN (
               SELECT student_id FROM class_enrollment WHERE class_id = ?
           )
           ORDER BY u.fullname''',
        (session['organization_id'], class_id)
    )

    return jsonify({
        'success': True,
        'enrolled': [dict(s) for s in enrolled],
        'available': [dict(s) for s in available]
    })    

# Add student to class
@app.route('/add-to-class/<int:class_id>/<int:student_id>', methods=['POST'])
def add_to_class(class_id, student_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    db.execute_query(
        'INSERT OR IGNORE INTO class_enrollment (class_id, student_id) VALUES (?, ?)',
        (class_id, student_id)
    )
    return jsonify({'success': True})

# Remove student from class
@app.route('/remove-from-class/<int:class_id>/<int:student_id>', methods=['POST'])
def remove_from_class(class_id, student_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    db.execute_query(
        'DELETE FROM class_enrollment WHERE class_id = ? AND student_id = ?',
        (class_id, student_id)
    )
    return jsonify({'success': True})

# Get classes for a teacher (used in programs/challenges modals)
@app.route('/my-classes')
def get_my_classes():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    classes = db.fetch_query(
        'SELECT class_id, name, subject FROM class WHERE teacher_id = ? ORDER BY name',
        (session['user_id'],)
    )
    return jsonify({'classes': [dict(c) for c in classes]})

# Toggle program availability for a class
@app.route('/toggle-program-class', methods=['POST'])
def toggle_program_class():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] != 'teacher':
        return jsonify({'success': False, 'message': 'Not authorized'})

    data = request.get_json()
    program_id = data.get('program_id')
    class_id = data.get('class_id')
    assign = data.get('assign')  # True = assign, False = remove

    # Verify teacher owns this program
    program = db.fetch_one(
        'SELECT * FROM program WHERE program_id = ? AND created_by = ?',
        (program_id, session['user_id'])
    )
    if not program:
        return jsonify({'success': False, 'message': 'Not authorized'})

    if assign:
        db.execute_query(
            'INSERT OR IGNORE INTO program_class (program_id, class_id) VALUES (?, ?)',
            (program_id, class_id)
        )
    else:
        db.execute_query(
            'DELETE FROM program_class WHERE program_id = ? AND class_id = ?',
            (program_id, class_id)
        )

    return jsonify({'success': True})

# Toggle challenge availability for a class
@app.route('/toggle-challenge-class', methods=['POST'])
def toggle_challenge_class():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] != 'teacher':
        return jsonify({'success': False, 'message': 'Not authorized'})

    data = request.get_json()
    challenge_id = data.get('challenge_id')
    class_id = data.get('class_id')
    assign = data.get('assign')

    challenge = db.fetch_one(
        'SELECT * FROM challenge WHERE challenge_id = ? AND created_by = ?',
        (challenge_id, session['user_id'])
    )
    if not challenge:
        return jsonify({'success': False, 'message': 'Not authorized'})

    if assign:
        db.execute_query(
            'INSERT OR IGNORE INTO challenge_class (challenge_id, class_id) VALUES (?, ?)',
            (challenge_id, class_id)
        )
    else:
        db.execute_query(
            'DELETE FROM challenge_class WHERE challenge_id = ? AND class_id = ?',
            (challenge_id, class_id)
        )

    return jsonify({'success': True})

# Get programs page
@app.route('/programs')
def get_programs():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    org_id = session.get('organization_id')

    # For students — only show programs assigned to their class
    if session['role'] == 'student':
        sql = '''
            SELECT p.*,
                u.fullname as creator_name,
                (SELECT COUNT(*) FROM enrollment e WHERE e.program_id = p.program_id) as enrolled_count,
                (SELECT COUNT(*) FROM enrollment e WHERE e.program_id = p.program_id AND e.student_id = ?) as is_enrolled
            FROM program p
            JOIN user u ON p.created_by = u.user_id
            JOIN program_class pc ON pc.program_id = p.program_id
            JOIN class_enrollment ce ON ce.class_id = pc.class_id AND ce.student_id = ?
            WHERE p.organization_id = ?
            GROUP BY p.program_id
            ORDER BY p.created_at DESC
        '''
        programs = db.fetch_query(sql, (session['user_id'], session['user_id'], org_id))
    else:
        # Teachers, admins see all org programs
        sql = '''
            SELECT p.*,
                u.fullname as creator_name,
                (SELECT COUNT(*) FROM enrollment e WHERE e.program_id = p.program_id) as enrolled_count,
                (SELECT COUNT(*) FROM enrollment e WHERE e.program_id = p.program_id AND e.student_id = ?) as is_enrolled
            FROM program p
            JOIN user u ON p.created_by = u.user_id
            WHERE p.organization_id = ?
            ORDER BY p.created_at DESC
        '''
        programs = db.fetch_query(sql, (session['user_id'], org_id))

    # Fetch files for each program
    programs_with_files = []
    for p in programs:
        files = db.fetch_query(
            'SELECT * FROM program_file WHERE program_id = ?', (p['program_id'],)
        )
        
        # For students, fetch which files they've completed
        files_with_progress = []
        for f in files:
            if session['role'] == 'student':
                done = db.fetch_one(
                    'SELECT progress_id FROM file_progress WHERE student_id = ? AND file_id = ?',
                    (session['user_id'], f['file_id'])
                )
                files_with_progress.append({**dict(f), 'completed': 1 if done else 0})
            else:
                files_with_progress.append({**dict(f), 'completed': 0})

        programs_with_files.append({**dict(p), 'files': files_with_progress})

    species = db.fetch_query('SELECT common_name FROM species ORDER BY common_name')
    return render_template('shared/programs.html', user=user, programs=programs_with_files, species=species)

# Mark a file as complete
@app.route('/complete-file/<int:file_id>', methods=['POST'])
def complete_file(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] != 'student':
        return jsonify({'success': False, 'message': 'Only students can mark progress'})

    # Check student is enrolled in the program this file belongs to
    program = db.fetch_one(
        '''SELECT p.program_id FROM program p
           JOIN program_file pf ON pf.program_id = p.program_id
           WHERE pf.file_id = ?''',
        (file_id,)
    )
    if not program:
        return jsonify({'success': False, 'message': 'File not found'})

    enrolled = db.fetch_one(
        'SELECT enrollment_id FROM enrollment WHERE student_id = ? AND program_id = ?',
        (session['user_id'], program['program_id'])
    )
    if not enrolled:
        return jsonify({'success': False, 'message': 'Not enrolled in this program'})

    # Mark file as complete (ignore if already done)
    db.execute_query(
        'INSERT OR IGNORE INTO file_progress (student_id, file_id) VALUES (?, ?)',
        (session['user_id'], file_id)
    )

    # Check if all files in this program are now complete
    total_files = db.fetch_one(
        'SELECT COUNT(*) as count FROM program_file WHERE program_id = ?',
        (program['program_id'],)
    )
    completed_files = db.fetch_one(
        '''SELECT COUNT(*) as count FROM file_progress fp
           JOIN program_file pf ON fp.file_id = pf.file_id
           WHERE pf.program_id = ? AND fp.student_id = ?''',
        (program['program_id'], session['user_id'])
    )

    program_completed = total_files['count'] == completed_files['count']

    # If all files done, mark enrollment as completed
    if program_completed:
        db.execute_query(
            '''UPDATE enrollment SET status = 'completed', completed_at = CURRENT_TIMESTAMP
               WHERE student_id = ? AND program_id = ?''',
            (session['user_id'], program['program_id'])
        )

    return jsonify({
        'success': True,
        'program_completed': program_completed,
        'completed_count': completed_files['count'],
        'total_count': total_files['count']
    })


# Unmark a file as complete
@app.route('/uncomplete-file/<int:file_id>', methods=['POST'])
def uncomplete_file(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] != 'student':
        return jsonify({'success': False, 'message': 'Only students can mark progress'})

    db.execute_query(
        'DELETE FROM file_progress WHERE student_id = ? AND file_id = ?',
        (session['user_id'], file_id)
    )

    # Revert program back to enrolled if it was completed
    program = db.fetch_one(
        '''SELECT p.program_id FROM program p
           JOIN program_file pf ON pf.program_id = p.program_id
           WHERE pf.file_id = ?''',
        (file_id,)
    )
    if program:
        db.execute_query(
            '''UPDATE enrollment SET status = 'enrolled', completed_at = NULL
               WHERE student_id = ? AND program_id = ?''',
            (session['user_id'], program['program_id'])
        )

    return jsonify({'success': True})

# Create a program (teachers only)
@app.route('/create-program', methods=['POST'])
def create_program():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] != 'teacher':
        return jsonify({'success': False, 'message': 'Only teachers can create programs'})

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    species_focus = request.form.get('species_focus', '').strip()
    duration = request.form.get('duration', '').strip()

    if not title or not description:
        return jsonify({'success': False, 'message': 'Title and description are required'})

    db.execute_query(
        'INSERT INTO program (title, description, species_focus, duration, created_by, organization_id) VALUES (?, ?, ?, ?, ?, ?)',
        (title, description, species_focus, duration, session['user_id'], session['organization_id'])
    )

    # Get the new program's ID
    program = db.fetch_one(
        'SELECT program_id FROM program WHERE created_by = ? ORDER BY created_at DESC LIMIT 1',
        (session['user_id'],)
    )
    program_id = program['program_id']

    # Handle file uploads
    files = request.files.getlist('files')
    for file in files:
        if file and file.filename:
            allowed = {'pdf', 'ppt', 'pptx', 'doc', 'docx'}
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
            if ext not in allowed:
                continue
            filename = secure_filename(file.filename)
            unique_filename = f"prog_{program_id}_{int(time.time())}_{filename}"
            os.makedirs(PROGRAM_FILES_FOLDER, exist_ok=True)
            file.save(os.path.join(PROGRAM_FILES_FOLDER, unique_filename))
            db.execute_query(
                'INSERT INTO program_file (program_id, filename, filepath) VALUES (?, ?, ?)',
                (program_id, filename, f"uploads/program-files/{unique_filename}")
            )

    return jsonify({'success': True, 'program_id': program_id})


# Enroll in a program (students only)
@app.route('/enroll/<int:program_id>', methods=['POST'])
def enroll_program(program_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] != 'student':
        return jsonify({'success': False, 'message': 'Only students can enroll'})

    # Check program exists and belongs to same org
    program = db.fetch_one(
        'SELECT * FROM program WHERE program_id = ? AND organization_id = ?',
        (program_id, session['organization_id'])
    )
    if not program:
        return jsonify({'success': False, 'message': 'Program not found'})

    # Check not already enrolled
    existing = db.fetch_one(
        'SELECT enrollment_id FROM enrollment WHERE student_id = ? AND program_id = ?',
        (session['user_id'], program_id)
    )
    if existing:
        return jsonify({'success': False, 'message': 'Already enrolled'})

    db.execute_query(
        'INSERT INTO enrollment (student_id, program_id) VALUES (?, ?)',
        (session['user_id'], program_id)
    )
    return jsonify({'success': True})


# Unenroll from a program
@app.route('/unenroll/<int:program_id>', methods=['POST'])
def unenroll_program(program_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] != 'student':
        return jsonify({'success': False, 'message': 'Only students can unenroll'})

    db.execute_query(
        'DELETE FROM enrollment WHERE student_id = ? AND program_id = ?',
        (session['user_id'], program_id)
    )
    return jsonify({'success': True})


# Delete a program (teacher who created it only)
@app.route('/delete-program/<int:program_id>', methods=['POST'])
def delete_program(program_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    program = db.fetch_one(
        'SELECT * FROM program WHERE program_id = ? AND created_by = ?',
        (program_id, session['user_id'])
    )
    if not program:
        return jsonify({'success': False, 'message': 'Not authorized or program not found'})

    db.execute_query('DELETE FROM program_file WHERE program_id = ?', (program_id,))
    db.execute_query('DELETE FROM enrollment WHERE program_id = ?', (program_id,))
    db.execute_query('DELETE FROM program WHERE program_id = ?', (program_id,))

    return jsonify({'success': True})

# Get activities page
@app.route('/activities')
def get_activities():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    org_id = session.get('organization_id')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Fetch challenges for this org
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if session['role'] in ['teacher', 'school-admin', 'principal', 'community-admin']:
        # Admins and teachers see all org challenges
        sql = '''
            SELECT c.*,
                u.fullname as creator_name,
                (SELECT COUNT(*) FROM challenge_submission cs 
                    WHERE cs.challenge_id = c.challenge_id) as submission_count,
                NULL as my_submission_id,
                CASE WHEN c.deadline < ? THEN 'expired' ELSE 'active' END as status
            FROM challenge c
            JOIN user u ON c.created_by = u.user_id
            WHERE c.organization_id = ?
            ORDER BY c.created_at DESC
        '''
        challenges = db.fetch_query(sql, (now, org_id))

    elif session['role'] == 'student':
        # Students only see challenges assigned to their class
        sql = '''
            SELECT c.*,
                u.fullname as creator_name,
                (SELECT COUNT(*) FROM challenge_submission cs 
                    WHERE cs.challenge_id = c.challenge_id) as submission_count,
                (SELECT submission_id FROM challenge_submission cs
                    WHERE cs.challenge_id = c.challenge_id AND cs.student_id = ?) as my_submission_id,
                CASE WHEN c.deadline < ? THEN 'expired' ELSE 'active' END as status
            FROM challenge c
            JOIN user u ON c.created_by = u.user_id
            JOIN challenge_class cc ON cc.challenge_id = c.challenge_id
            JOIN class_enrollment ce ON ce.class_id = cc.class_id AND ce.student_id = ?
            WHERE c.organization_id = ?
            GROUP BY c.challenge_id
            ORDER BY c.created_at DESC
        '''
        challenges = db.fetch_query(sql, (session['user_id'], now, session['user_id'], org_id))

    elif session['role'] == 'community-member':
        # Community members see challenges assigned to their org
        # (no class system for communities, so just org-scoped)
        sql = '''
            SELECT c.*,
                u.fullname as creator_name,
                (SELECT COUNT(*) FROM challenge_submission cs 
                    WHERE cs.challenge_id = c.challenge_id) as submission_count,
                (SELECT submission_id FROM challenge_submission cs
                    WHERE cs.challenge_id = c.challenge_id AND cs.student_id = ?) as my_submission_id,
                CASE WHEN c.deadline < ? THEN 'expired' ELSE 'active' END as status
            FROM challenge c
            JOIN user u ON c.created_by = u.user_id
            WHERE c.organization_id = ?
            ORDER BY c.created_at DESC
        '''
        challenges = db.fetch_query(sql, (session['user_id'], now, org_id))

    else:
        challenges = []

    # Stats
    active_count = sum(1 for c in challenges if c['status'] == 'active')

    if session['role'] in ['student', 'community-member']:
        completed_count = db.fetch_one(
            'SELECT COUNT(*) as count FROM challenge_submission WHERE student_id = ?',
            (session['user_id'],)
        )['count']
        points = user['points'] or 0
    else:
        completed_count = db.fetch_one(
            '''SELECT COUNT(*) as count FROM challenge_submission cs
               JOIN challenge c ON cs.challenge_id = c.challenge_id
               WHERE c.organization_id = ?''',
            (org_id,)
        )['count']
        points = None

    # Leaderboard (org-wide, top 10)
    leaderboard = db.fetch_query(
        '''SELECT fullname, points, avatar, role FROM user
           WHERE organization_id = ? AND role IN ('student', 'community-member')
           ORDER BY points DESC LIMIT 10''',
        (org_id,)
    )

    # Species list for modal dropdown
    species = db.fetch_query('SELECT common_name FROM species ORDER BY common_name')

    return render_template('shared/activity.html',
        user=user,
        challenges=[dict(c) for c in challenges],
        active_count=active_count,
        completed_count=completed_count,
        points=points,
        leaderboard=leaderboard,
        species=species
    )


@app.route('/get-program-classes/<int:program_id>')
def get_program_classes(program_id):
    if 'user_id' not in session:
        return jsonify({'success': False})
    rows = db.fetch_query(
        'SELECT class_id FROM program_class WHERE program_id = ?', (program_id,)
    )
    return jsonify({'class_ids': [r['class_id'] for r in rows]})


@app.route('/get-challenge-classes/<int:challenge_id>')
def get_challenge_classes(challenge_id):
    if 'user_id' not in session:
        return jsonify({'success': False})
    rows = db.fetch_query(
        'SELECT class_id FROM challenge_class WHERE challenge_id = ?', (challenge_id,)
    )
    return jsonify({'class_ids': [r['class_id'] for r in rows]})

# Create a challenge
@app.route('/create-challenge', methods=['POST'])
def create_challenge():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['teacher', 'community-admin']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data = request.get_json()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    points = data.get('points')
    duration = data.get('duration_days')
    species_focus = data.get('species_focus', '').strip()

    if not title or not description or not points or not duration:
        return jsonify({'success': False, 'message': 'All fields are required'})

    deadline = (datetime.now() + timedelta(days=int(duration))).strftime('%Y-%m-%d %H:%M:%S')

    db.execute_query(
        '''INSERT INTO challenge (title, description, points, duration_days, deadline, species_focus, created_by, organization_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (title, description, int(points), int(duration), deadline,
         species_focus, session['user_id'], session['organization_id'])
    )
    return jsonify({'success': True})


# Submit challenge evidence
@app.route('/submit-challenge/<int:challenge_id>', methods=['POST'])
def submit_challenge(challenge_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['student', 'community-member']:
        return jsonify({'success': False, 'message': 'Only participants can submit'})

    # Check challenge exists and belongs to same org
    challenge = db.fetch_one(
        'SELECT * FROM challenge WHERE challenge_id = ? AND organization_id = ?',
        (challenge_id, session['organization_id'])
    )
    if not challenge:
        return jsonify({'success': False, 'message': 'Challenge not found'})

    # Check deadline
    if datetime.now() > datetime.strptime(challenge['deadline'], '%Y-%m-%d %H:%M:%S'):
        return jsonify({'success': False, 'message': 'Challenge deadline has passed'})

    # Check not already submitted
    existing = db.fetch_one(
        'SELECT submission_id FROM challenge_submission WHERE challenge_id = ? AND student_id = ?',
        (challenge_id, session['user_id'])
    )
    if existing:
        return jsonify({'success': False, 'message': 'Already submitted'})

    # Handle media upload
    media_path = None
    if 'media' in request.files:
        file = request.files['media']
        if file and file.filename:
            allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov'}
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
            if ext not in allowed:
                return jsonify({'success': False, 'message': 'File type not allowed'})
            filename = secure_filename(file.filename)
            unique_filename = f"challenge_{challenge_id}_{session['user_id']}_{int(time.time())}_{filename}"
            os.makedirs(CHALLENGE_MEDIA_FOLDER, exist_ok=True)
            file.save(os.path.join(CHALLENGE_MEDIA_FOLDER, unique_filename))
            media_path = f"uploads/challenge-media/{unique_filename}"

    description = request.form.get('description', '').strip()

    if not media_path and not description:
        return jsonify({'success': False, 'message': 'Please provide evidence (photo/video or description)'})

    # Save submission
    db.execute_query(
        '''INSERT INTO challenge_submission (challenge_id, student_id, media_path, description)
           VALUES (?, ?, ?, ?)''',
        (challenge_id, session['user_id'], media_path, description)
    )

    # Award points immediately (auto-complete)
    db.execute_query(
        'UPDATE user SET points = points + ? WHERE user_id = ?',
        (challenge['points'], session['user_id'])
    )

    return jsonify({
        'success': True,
        'points_earned': challenge['points'],
        'new_total': db.fetch_one('SELECT points FROM user WHERE user_id = ?', (session['user_id'],))['points']
    })


# Delete a challenge (creator only)
@app.route('/delete-challenge/<int:challenge_id>', methods=['POST'])
def delete_challenge(challenge_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    challenge = db.fetch_one(
        'SELECT * FROM challenge WHERE challenge_id = ? AND created_by = ?',
        (challenge_id, session['user_id'])
    )
    if not challenge:
        return jsonify({'success': False, 'message': 'Not authorized'})

    # Revoke points from all submitters
    submissions = db.fetch_query(
        'SELECT student_id FROM challenge_submission WHERE challenge_id = ?',
        (challenge_id,)
    )
    for s in submissions:
        db.execute_query(
            'UPDATE user SET points = MAX(0, points - ?) WHERE user_id = ?',
            (challenge['points'], s['student_id'])
        )

    db.execute_query('DELETE FROM challenge_submission WHERE challenge_id = ?', (challenge_id,))
    db.execute_query('DELETE FROM challenge WHERE challenge_id = ?', (challenge_id,))

    return jsonify({'success': True})

#Get Creatinv Canvas page
@app.route('/creative-canvas')
def get_creative_canvas():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'], ))
    return render_template('shared/creative-canvas.html', user = user)

# Get messages page
@app.route('/messages')
def get_messages():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    
    sql = '''
        SELECT 
            u.user_id, u.fullname, u.role, u.avatar,
            m.body as last_message,
            m.sent_at as last_time,
            (SELECT COUNT(*) FROM message 
             WHERE sender_id = u.user_id 
             AND receiver_id = ? 
             AND is_read = 0) as unread_count
        FROM user u
        JOIN message m ON m.message_id = (
            SELECT message_id FROM message
            WHERE (sender_id = u.user_id AND receiver_id = ?)
               OR (sender_id = ? AND receiver_id = u.user_id)
            ORDER BY sent_at DESC LIMIT 1
        )
        WHERE u.user_id != ?
        GROUP BY u.user_id
        ORDER BY last_time DESC
    '''
    conversations = db.fetch_query(sql, (
        session['user_id'], session['user_id'],
        session['user_id'], session['user_id']
    ))
    
    return render_template('shared/messages.html', user=user, conversations=conversations)


# Get all messages between current user and another user
@app.route('/get-messages/<int:other_user_id>')
def get_conversation(other_user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    me = session['user_id']
    
    # Mark incoming messages as read
    db.execute_query(
        'UPDATE message SET is_read = 1 WHERE sender_id = ? AND receiver_id = ?',
        (other_user_id, me)
    )
    
    sql = '''
        SELECT m.message_id, m.body, m.sent_at, m.sender_id,
               u.fullname as sender_name, u.avatar as sender_avatar
        FROM message m
        JOIN user u ON m.sender_id = u.user_id
        WHERE (m.sender_id = ? AND m.receiver_id = ?)
           OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.sent_at ASC
    '''
    messages = db.fetch_query(sql, (me, other_user_id, other_user_id, me))
    other_user = db.fetch_one(
        'SELECT user_id, fullname, role, avatar FROM user WHERE user_id = ?', 
        (other_user_id,)
    )
    
    return jsonify({
        'success': True,
        'messages': [dict(m) for m in messages],
        'other_user': dict(other_user)
    })

# Send a message
@app.route('/send-message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    body        = request.form.get('body', '').strip()
    receiver_id = request.form.get('receiver_id')
    attachment_path = None

    if not receiver_id:
        return jsonify({'success': False, 'message': 'No recipient specified'})
    if not body and 'attachment' not in request.files:
        return jsonify({'success': False, 'message': 'Message cannot be empty'})

    # Handle file attachment
    if 'attachment' in request.files:
        file = request.files['attachment']
        if file and file.filename != '':
            allowed_msg = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if ext not in allowed_msg:
                return jsonify({'success': False, 'message': 'File type not allowed'})
            filename        = secure_filename(file.filename)
            unique_filename = f"msg_{session['user_id']}_{int(time.time())}_{filename}"
            os.makedirs(MESSAGE_ATTACHMENT_FOLDER, exist_ok=True)
            file.save(os.path.join(MESSAGE_ATTACHMENT_FOLDER, unique_filename))
            attachment_path = f"uploads/message-attachments/{unique_filename}"

    sql = 'INSERT INTO message (sender_id, receiver_id, body, attachment) VALUES (?, ?, ?, ?)'
    db.execute_query(sql, (session['user_id'], receiver_id, body, attachment_path))

    return jsonify({
        'success': True,
        'sent_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'attachment': attachment_path
    })
    
# Search users to start a new conversation
@app.route('/search-users')
def search_users():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'users': []})
    
    sql = '''SELECT user_id, fullname, role, avatar FROM user 
             WHERE fullname LIKE ? AND user_id != ? LIMIT 10'''
    users = db.fetch_query(sql, (f'%{query}%', session['user_id']))
    
    return jsonify({'users': [dict(u) for u in users]})

#Get my profile details
@app.route('/my-profile')
def get_my_profile():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    org = None
    member_count = 0
    org_sightings_count = 0

    if user['organization_id']:
        org = db.fetch_one(
            'SELECT * FROM organization WHERE organization_id = ?',
            (user['organization_id'],)
        )
        if user['role'] in ['school-admin', 'community-admin'] and org:
            mc = db.fetch_one(
                'SELECT COUNT(*) as count FROM user WHERE organization_id = ? AND user_id != ?',
                (user['organization_id'], session['user_id'])
            )
            member_count = mc['count'] if mc else 0

            sc = db.fetch_one(
                '''SELECT COUNT(*) as count FROM sighting s
                   JOIN user u ON s.user_id = u.user_id
                   WHERE u.organization_id = ?''',
                (user['organization_id'],)
            )
            org_sightings_count = sc['count'] if sc else 0

    sightings_count = db.fetch_one(
        'SELECT COUNT(*) as count FROM sighting WHERE user_id = ?',
        (session['user_id'],)
    )

    return render_template(
        'shared/my-profile.html',
        user=user, org=org,
        sightings_count=sightings_count['count'],
        member_count=member_count,
        org_sightings_count=org_sightings_count
    )

#Handling profile updates
@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    try:
        data = request.get_json()
        fullname = data.get('fullname')
        phone = data.get('phone')
        location = data.get('location')
        email = data.get('email')
        
        #Check if new email is used by another user
        existing = db.fetch_one('SELECT user_id FROM user WHERE email=? AND user_id != ?', (email, session['user_id']))
        if existing:
            return jsonify({'success': False, 'message': 'This email is already use'})
        
        sql = 'UPDATE user SET fullname = ?, email=?, phone = ?, location = ? WHERE user_id = ?'
        db.execute_query(sql, (fullname, email,  phone, location, session['user_id']))
        #Updating session fullname
        session['fullname'] = fullname
        
        return jsonify({'success': True})
    except Exception as e:
        print('update_profile error: ', e)
        return jsonify({'success': False, 'message': str(e)})

#Handling school and community profile updates    
@app.route('/update-org-profile', methods=['POST'])
def update_org_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'community-admin']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data    = request.get_json()
    name    = data.get('name', '').strip()
    type_   = data.get('type', '').strip()
    email   = data.get('email', '').strip()
    address = data.get('address', '').strip()

    if not name or not email:
        return jsonify({'success': False, 'message': 'Name and email are required'})

    db.execute_query(
        'UPDATE organization SET name=?, type=?, email=?, address=? WHERE organization_id=?',
        (name, type_, email, address, session['organization_id'])
    )
    return jsonify({'success': True})


#Handle Avatar (profile photo) change
@app.route('/update-avatar', methods=['POST'])
def update_avatar():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['avatar']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Only jpg, jpeg, png allowed'})
    
    filename = secure_filename(file.filename)
    unique_filename = f"avatar_{session['user_id']}_{int(time.time())}_{filename}"
    os.makedirs(AVATAR_FOLDER, exist_ok=True)
    save_path = os.path.join(AVATAR_FOLDER, unique_filename)
    file.save(save_path)
    
    avatar_path = f"uploads/avatars/{unique_filename}"
    db.execute_query('UPDATE user SET avatar = ? WHERE user_id = ?', (avatar_path, session['user_id']))
    
    return jsonify({'success': True, 'avatar_url': url_for('static', filename=avatar_path)})

#Handling school and community profile avatar changes
@app.route('/update-org-avatar', methods=['POST'])
def update_org_avatar():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'community-admin']:
        return jsonify({'success': False, 'message': 'Not authorized'})
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    file = request.files['avatar']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid file'})

    org_id          = session.get('organization_id')
    filename        = secure_filename(file.filename)
    unique_filename = f"org_{org_id}_{int(time.time())}_{filename}"
    file.save(os.path.join(AVATAR_FOLDER, unique_filename))

    avatar_path = f"uploads/avatars/{unique_filename}"
    db.execute_query(
        'UPDATE organization SET avatar=? WHERE organization_id=?',
        (avatar_path, org_id)
    )
    return jsonify({'success': True, 'avatar_url': url_for('static', filename=avatar_path)})
       
#Handling password change
@app.route('/change-password', methods = ['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    data = request.get_json()
    current = data.get('currentPassword')
    new_pass = data.get('newPassword')
    
    user = db.fetch_one('SELECT password FROM user WHERE user_id = ?', (session['user_id'], ))
    
    if not check_password_hash(user['password'], current):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    hashed = generate_password_hash(new_pass)
    db.execute_query('UPDATE user SET password=? WHERE user_id=?', (hashed, session['user_id']))
    
    return jsonify({'success': True})

#Deleting account logic
@app.route('/delete-account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user = db.fetch_one('SELECT role, organization_id FROM user WHERE user_id = ?', (session['user_id'], ))
    
    #IF admin, delete entire organization and all its members first
    if user['role'] in ['school-admin', 'community-admin'] and user['organization_id']:
        org_id = user['organization_id']
        
        #Get all users in this organization
        members = db.fetch_query('SELECT user_id FROM user WHERE organization_id = ?', (org_id, ))
        
        for member in members:
            mid = member['user_id']
            db.execute_query('DELETE FROM sighting WHERE user_id = ?', (mid, ))
            db.execute_query('DELETE FROM message WHERE sender_id = ? OR receiver_id = ?', (mid, mid))
            db.execute_query('DELETE FROM user WHERE user_id = ?', (mid, ))
            
        #Delete registration records for this org
        db.execute_query('DELETE FROM registration WHERE organization_id = ?', (org_id, ))
        
        #Delete the organization
        db.execute_query('DELETE FROM organization WHERE organization_id = ?', (org_id, ))
        
    else:
        #Just delete this user's data
        #Delete user's sightings first (foreign key)
        db.execute_query('DELETE FROM sighting WHERE user_id = ?', (session['user_id'], ))
        #Delete user's messages
        db.execute_query('DELETE FROM message WHERE sender_id = ? OR receiver_id = ?', (session['user_id'], session['user_id']))
        #Delete user
        db.execute_query('DELETE FROM user WHERE user_id = ?', (session['user_id'], ))
        
    session.clear()
    return jsonify({'success': True})

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
    
    #Fetch sightings based on role
    if user['role'] == 'system-admin':
        #System admin sees all sightings
        sql = '''SELECT s.*, sp.common_name, sp.species_id as sp_id,
            u.fullname as reporter_name, u.role as reporter_role, u.avatar as reporter_avatar
            FROM sighting s
            JOIN species sp ON s.species_id =sp.species_id
            JOIN user u ON s.user_id = u.user_id
            ORDER BY s.submitted_at DESC'''
        sightings = db.fetch_query(sql)
    elif user['role'] in ['teacher', 'school-admin', 'principal']:
        #School roles see sightings from their organization
        sql = '''SELECT s.*, sp.common_name, sp.species_id as sp_id,
            u.fullname as reporter_name, u.role as reporter_role, u.avatar as reporter_avatar
            FROM sighting s
            JOIN species sp ON s.species_id = sp.species_id
            JOIN user u ON s.user_id = u.user_id
            WHERE u.organization_id = ?
            ORDER BY s.submitted_at DESC'''
        sightings = db.fetch_query(sql, (user['organization_id'], ))
    elif user['role'] == 'community-admin':
        #Community admin sees sightings from their community
        sql = '''SELECT s.*, sp.common_name, sp.species_id as sp_id,
            u.fullname as reporter_name, u.role as reporter_role, u.avatar as reporter_avatar
            FROM sighting s
            JOIN species sp ON s.species_id = sp.species_id
            JOIN user u ON s.user_id = u.user_id
            WHERE u.organization_id = ?
            ORDER BY s.submitted_at DESC'''
        sightings = db.fetch_query(sql, (user['organization_id'], ))
    else:
        #Students, community members see only their own
        sql = '''SELECT s.*, sp.common_name, sp.species_id as sp_id,
        u.fullname as reporter_name, u.role as reporter_role, u.avatar as reporter_avatar
        FROM sighting s
        JOIN species sp ON s.species_id = sp.species_id
        JOIN user u ON s.user_id = u.user_id
        WHERE s.user_id = ?
        ORDER BY s.submitted_at DESC'''
        sightings = db.fetch_query(sql, (session['user_id'], ))
        
    return render_template('shared/sighting-reports-view.html', user=user, sightings = sightings)

#Deleting sighting reports logic
@app.route('/delete-sighting/<int:sighting_id>', methods=['POST'])
def delete_sighting(sighting_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    #Make sure the sighting belongs to this user or they-re an admin
    allowed_roles = ['teacher', 'school-admin', 'principal', 'community-admin']
    if session['role'] not in  allowed_roles:
        sighting = db.fetch_one('SELECT user_id FROM sighting WHERE sighting_id = ?', (sighting_id, ))
        if not sighting or sighting['user_id'] != session['user_id']:
            return jsonify({'success': False, 'message': 'Not authorized'})
    
    db.execute_query('DELETE FROM sighting WHERE sighting_id = ?', (sighting_id, ))
    return jsonify({'success': True})
  
# Inline add member (replaces the separate register-member POST for admin use)
@app.route('/add-member', methods=['POST'])
def add_member():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'principal', 'community-admin']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data = request.get_json()
    role      = data.get('role')
    full_name = data.get('full_name', '').strip()
    email     = data.get('email', '').strip()
    access_code = data.get('access_code', '').strip()
    org_id    = session.get('organization_id')

    if not full_name or not email or not access_code:
        return jsonify({'success': False, 'message': 'All fields are required'})

    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        return jsonify({'success': False, 'message': 'Please enter a valid email address'})
        
    # Only one principal allowed
    if role == 'principal':
        existing = db.fetch_one(
            "SELECT user_id FROM user WHERE role = 'principal' AND organization_id = ?",
            (org_id,)
        )
        if existing:
            return jsonify({'success': False, 'message': 'A principal is already registered for this school'})
        existing_reg = db.fetch_one(
            "SELECT id FROM registration WHERE role = 'principal' AND organization_id = ?",
            (org_id,)
        )
        if existing_reg:
            return jsonify({'success': False, 'message': 'A principal invitation already exists'})

    # Check email not already invited
    existing_email = db.fetch_one('SELECT id FROM registration WHERE email = ?', (email,))
    if existing_email:
        return jsonify({'success': False, 'message': 'This email already has a pending invitation'})

    # Check email not already registered
    existing_user = db.fetch_one('SELECT user_id FROM user WHERE email = ?', (email,))
    if existing_user:
        return jsonify({'success': False, 'message': 'An account with this email already exists'})

    db.execute_query(
        'INSERT INTO registration (email, full_name, role, access_code, organization_id) VALUES (?, ?, ?, ?, ?)',
        (email, full_name, role, access_code, org_id)
    )
    return jsonify({'success': True})

# Revoke a pending invitation
@app.route('/revoke-invitation/<int:reg_id>', methods=['POST'])
def revoke_invitation(reg_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'principal', 'community-admin']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    db.execute_query(
        'DELETE FROM registration WHERE id = ? AND organization_id = ?',
        (reg_id, session['organization_id'])
    )
    return jsonify({'success': True})
    
# Manage Staff (teachers + principals) for school-admin and principal
@app.route('/manage-staff')
def get_staff_details():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] not in ['school-admin', 'principal', 'system-admin']:
        return abort(403)
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    if session['role'] == 'system-admin':
        members = db.fetch_query(
            "SELECT * FROM user WHERE role IN ('teacher', 'principal') ORDER BY role"
        )
    else:
        members = db.fetch_query(
            "SELECT * FROM user WHERE role IN ('teacher', 'principal') AND organization_id = ?",
            (session['organization_id'],)
        )

    # Pending registrations
    pending = db.fetch_query(
        '''SELECT * FROM registration 
           WHERE organization_id = ? AND role IN ('teacher', 'principal') AND status = 'pending'
           ORDER BY id DESC''',
        (session['organization_id'],)
    ) if session['role'] != 'system-admin' else []

    total = len(members)
    active = sum(1 for m in members if m['status'] == 'active')
    inactive = total - active
    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    new_this_month = sum(1 for m in members if m['created_at'] and m['created_at'][:10] >= month_ago)

    # Check if principal already exists
    has_principal = db.fetch_one(
        "SELECT user_id FROM user WHERE role = 'principal' AND organization_id = ?",
        (session['organization_id'],)
    ) is not None

    return render_template('shared/manage-users.html',
        user=user, members=members, pending=pending,
        manage_type='staff', has_principal=has_principal,
        total=total, active=active, inactive=inactive, new_this_month=new_this_month
    )

# Manage Students — update to include pending + inline add
@app.route('/manage-students')
def get_students_details():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] not in ['school-admin', 'principal', 'system-admin']:
        return abort(403)
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    if session['role'] == 'system-admin':
        members = db.fetch_query("SELECT * FROM user WHERE role = 'student'")
    else:
        members = db.fetch_query(
            "SELECT * FROM user WHERE role = 'student' AND organization_id = ?",
            (session['organization_id'],)
        )

    pending = db.fetch_query(
        '''SELECT * FROM registration 
           WHERE organization_id = ? AND role = 'student' AND status = 'pending'
           ORDER BY id DESC''',
        (session['organization_id'],)
    ) if session['role'] != 'system-admin' else []

    total = len(members)
    active = sum(1 for m in members if m['status'] == 'active')
    inactive = total - active
    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    new_this_month = sum(1 for m in members if m['created_at'] and m['created_at'][:10] >= month_ago)

    return render_template('shared/manage-users.html',
        user=user, members=members, pending=pending,
        manage_type='students', has_principal=False,
        total=total, active=active, inactive=inactive, new_this_month=new_this_month
    )

#Retrieving Community members details for community admin
@app.route('/manage-members')
def get_members_details():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'], ))
    
    sql = "SELECT * FROM user WHERE role = 'community-member' AND organization_id = ?"
    members = db.fetch_query(sql, (session['organization_id'],))
    total = len(members)
    active = sum(1 for m in members if m['status'] == 'active')
    inactive = total -active
    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    new_this_month = sum(1 for m in members if m['created_at'] and m['created_at'][:10] >= month_ago)

    return render_template('shared/manage-users.html', user=user, members=members, manage_type='members',
        total=total, active=active, inactive=inactive, new_this_month=new_this_month)

#Retrieving all users data for system admin
@app.route('/manage-all-users')
def get_all_users():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] != 'system-admin':
        return abort(403)
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    members = db.fetch_query("SELECT * FROM user ORDER BY role")
    total = len(members)
    active = sum(1 for m in members if m['status'] == 'active')
    inactive = total -active
    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    new_this_month = sum(1 for m in members if m['created_at'] and m['created_at'][:10] >= month_ago)

    return render_template('shared/manage-users.html', user=user, members=members, manage_type='all-users',
        total=total, active=active, inactive=inactive, new_this_month=new_this_month)

#Handling user record deletion 
@app.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'principal', 'community-admin', 'system-admin']:
        return jsonify({'success': False, 'message': 'Not authorized'})
    if user_id == session['user_id']:
        return jsonify({'success': False, 'message': 'Use account settings to delete your own account'})
    
    db.execute_query('DELETE FROM sighting WHERE user_id = ?', (user_id,))
    db.execute_query('DELETE FROM message WHERE sender_id = ? OR receiver_id = ?', (user_id, user_id))
    db.execute_query('DELETE FROM user WHERE user_id = ?', (user_id,))
    
    return jsonify({'success': True})

#Handling user record update made by admins
@app.route('/update-user-status', methods=['POST'])
def update_user_status():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['school-admin', 'principal', 'community-admin', 'system-admin']:
        return jsonify({'success': False, 'message': 'Not authorized'})
    data = request.get_json()
    db.execute_query(
        'UPDATE user SET status = ? WHERE user_id = ?',
        (data['status'], data['user_id'])
    )
    return jsonify({'success': True})

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