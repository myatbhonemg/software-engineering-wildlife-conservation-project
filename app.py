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

#Make enrolled_class available in every template for the student sidebar link.
@app.context_processor
def inject_enrolled_class():
    if session.get('role') == 'student' and session.get('user_id'):
        enrolled_class = db.fetch_one(
            'SELECT class_id FROM class_enrollment WHERE student_id = ? LIMIT 1',
            (session['user_id'],)
        )
        return {'enrolled_class': enrolled_class}
    return {'enrolled_class': None}

#Handling file uploads folders and extensions
UPLOAD_FOLDER = 'static/uploads/sightings'
AVATAR_FOLDER = 'static/uploads/avatars'
MESSAGE_ATTACHMENT_FOLDER = 'static/uploads/message-attachments'
PROGRAM_FILES_FOLDER = 'static/uploads/program-files'
CHALLENGE_MEDIA_FOLDER = 'static/uploads/challenge-media'
CREATIVE_CANVAS_FOLDER = 'static/uploads/creative-canvas'



ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Function to auto complete Syllabus activity/program/sighting
def auto_complete_syllabus_activity(student_id, activity_type, linked_id=None):
    classes = db.fetch_query(
        'SELECT class_id FROM class_enrollment WHERE student_id = ?',
        (student_id,)
    )

    for cls in classes:
        class_id = cls['class_id']

        if activity_type == 'sighting':
            # linked_id is now species_id for sighting type
            if linked_id:
                activities = db.fetch_query('''
                    SELECT sa.activity_id
                    FROM syllabus_activity sa
                    JOIN syllabus_topic st ON sa.topic_id = st.topic_id
                    WHERE st.class_id = ?
                    AND sa.activity_type = 'sighting'
                    AND sa.linked_species_id = ?
                    AND sa.activity_id NOT IN (
                        SELECT activity_id FROM syllabus_activity_completion
                        WHERE student_id = ?
                    )
                ''', (class_id, linked_id, student_id))
            else:
                # No species specified — skip, don't auto-complete anything
                continue

        elif activity_type == 'program' and linked_id:
            activities = db.fetch_query('''
                SELECT sa.activity_id
                FROM syllabus_activity sa
                JOIN syllabus_topic st ON sa.topic_id = st.topic_id
                WHERE st.class_id = ?
                AND sa.activity_type = 'program'
                AND sa.linked_program_id = ?
                AND sa.activity_id NOT IN (
                    SELECT activity_id FROM syllabus_activity_completion
                    WHERE student_id = ?
                )
            ''', (class_id, linked_id, student_id))

        elif activity_type == 'challenge' and linked_id:
            activities = db.fetch_query('''
                SELECT sa.activity_id
                FROM syllabus_activity sa
                JOIN syllabus_topic st ON sa.topic_id = st.topic_id
                WHERE st.class_id = ?
                AND sa.activity_type = 'challenge'
                AND sa.linked_challenge_id = ?
                AND sa.activity_id NOT IN (
                    SELECT activity_id FROM syllabus_activity_completion
                    WHERE student_id = ?
                )
            ''', (class_id, linked_id, student_id))

        else:
            continue

        for act in activities:
            db.execute_query(
                '''INSERT OR IGNORE INTO syllabus_activity_completion
                   (activity_id, student_id) VALUES (?, ?)''',
                (act['activity_id'], student_id)
            )

#Handling the route to home page
@app.route('/home')
def home():
    sql = 'SELECT * FROM species'
    species = db.fetch_query(sql)

    school_count = db.fetch_one(
        "SELECT COUNT(*) as count FROM organization WHERE category = 'school'"
    )['count']

    community_member_count = db.fetch_one(
        "SELECT COUNT(*) as count FROM user WHERE role = 'community-member'"
    )['count']

    sighting_count = db.fetch_one(
        "SELECT COUNT(*) as count FROM sighting"
    )['count']

    species_count = db.fetch_one(
        "SELECT COUNT(*) as count FROM species"
    )['count']

    recent_sightings = db.fetch_query('''
        SELECT s.location, s.sighting_date, s.photo, s.description, s.count,
            sp.common_name, sp.status,
            u.fullname as reporter_name,
            o.name as school_name, o.category as org_category
        FROM sighting s
        JOIN species sp ON s.species_id = sp.species_id
        JOIN user u ON s.user_id = u.user_id
        LEFT JOIN organization o ON u.organization_id = o.organization_id
        ORDER BY s.submitted_at DESC
        LIMIT 6
    ''')

    return render_template("home.html",
        species=species,
        school_count=school_count,
        community_member_count=community_member_count,
        sighting_count=sighting_count,
        species_count=species_count,
        recent_sightings=recent_sightings
    )

#Redirecting to home page if no path provided
@app.route('/')
def home1():
    return redirect(url_for('home'))


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
    
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    sighting_count = db.fetch_one(
        'SELECT COUNT(*) as count FROM sighting WHERE user_id = ?',
        (session['user_id'],)
    )['count']

    challenges_joined = db.fetch_one(
        'SELECT COUNT(*) as count FROM challenge_submission WHERE student_id = ?',
        (session['user_id'],)
    )['count']

    programs_enrolled = db.fetch_one(
        'SELECT COUNT(*) as count FROM enrollment WHERE student_id = ?',
        (session['user_id'],)
    )['count']

    programs_completed = db.fetch_one(
        "SELECT COUNT(*) as count FROM enrollment WHERE student_id = ? AND status = 'completed'",
        (session['user_id'],)
    )['count']
    
    return render_template('student-dashboard.html',
        user=user,
        sighting_count=sighting_count,
        challenges_joined=challenges_joined,
        programs_enrolled=programs_enrolled,
        programs_completed=programs_completed,
    )


#Retriving teacher's data from DB and filling its dashboard
@app.route('/dashboard/teacher')
def teacher_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    # Students across all classes
    student_count = db.fetch_one('''
        SELECT COUNT(DISTINCT ce.student_id) as count
        FROM class_enrollment ce
        JOIN class c ON ce.class_id = c.class_id
        WHERE c.teacher_id = ?
    ''', (session['user_id'],))['count']

    # Sightings from students
    sighting_count = db.fetch_one('''
        SELECT COUNT(*) as count FROM sighting s
        WHERE s.user_id IN (
            SELECT DISTINCT ce.student_id
            FROM class_enrollment ce
            JOIN class c ON ce.class_id = c.class_id
            WHERE c.teacher_id = ?
        )
    ''', (session['user_id'],))['count']

    # Active challenges
    active_challenges = db.fetch_one(
        "SELECT COUNT(*) as count FROM challenge WHERE created_by = ? AND deadline >= datetime('now')",
        (session['user_id'],)
    )['count']

    # Programs created
    programs_count = db.fetch_one(
        'SELECT COUNT(*) as count FROM program WHERE created_by = ?',
        (session['user_id'],)
    )['count']

    # Classes
    class_count = db.fetch_one(
        'SELECT COUNT(*) as count FROM class WHERE teacher_id = ?',
        (session['user_id'],)
    )['count']

    # Pending (ungraded) challenge submissions across teacher's challenges
    pending_grades = db.fetch_one('''
        SELECT COUNT(*) as count
        FROM challenge_submission cs
        JOIN challenge c ON cs.challenge_id = c.challenge_id
        LEFT JOIN assessment_grade ag ON ag.submission_id = cs.submission_id
        WHERE c.created_by = ? AND ag.grade_id IS NULL
    ''', (session['user_id'],))['count']

    # Recent sightings from students (last 5)
    recent_sightings = db.fetch_query('''
        SELECT s.sighting_date, s.location, s.count,
               sp.common_name, u.fullname as student_name
        FROM sighting s
        JOIN species sp ON s.species_id = sp.species_id
        JOIN user u ON s.user_id = u.user_id
        JOIN class_enrollment ce ON ce.student_id = u.user_id
        JOIN class c ON ce.class_id = c.class_id
        WHERE c.teacher_id = ?
        ORDER BY s.submitted_at DESC
        LIMIT 5
    ''', (session['user_id'],))

    # Recent challenge submissions (last 5)
    recent_submissions = db.fetch_query('''
        SELECT cs.submitted_at, c.title as challenge_title,
               u.fullname as student_name, c.challenge_id,
               ag.score
        FROM challenge_submission cs
        JOIN challenge c ON cs.challenge_id = c.challenge_id
        JOIN user u ON cs.student_id = u.user_id
        LEFT JOIN assessment_grade ag ON ag.submission_id = cs.submission_id
        WHERE c.created_by = ?
        ORDER BY cs.submitted_at DESC
        LIMIT 5
    ''', (session['user_id'],))

    # My classes with student counts
    my_classes = db.fetch_query('''
        SELECT c.class_id, c.name, c.subject,
               COUNT(ce.student_id) as student_count
        FROM class c
        LEFT JOIN class_enrollment ce ON ce.class_id = c.class_id
        WHERE c.teacher_id = ?
        GROUP BY c.class_id
        ORDER BY c.name
    ''', (session['user_id'],))

    return render_template('teacher-dashboard.html',
        user=user,
        student_count=student_count,
        sighting_count=sighting_count,
        active_challenges=active_challenges,
        programs_count=programs_count,
        class_count=class_count,
        pending_grades=pending_grades,
        recent_sightings=[dict(s) for s in recent_sightings],
        recent_submissions=[dict(s) for s in recent_submissions],
        my_classes=[dict(c) for c in my_classes]
    )


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
    
    if user['role'] != 'system-admin':
        return redirect(url_for(f'/dashboard/{user["role"]}'))

    total_schools = db.fetch_one(
        "SELECT COUNT(*) as count FROM organization WHERE category = 'school'"
    )['count']

    total_communities = db.fetch_one(
        "SELECT COUNT(*) as count FROM organization WHERE category = 'community'"
    )['count']

    total_users = db.fetch_one(
        "SELECT COUNT(*) as count FROM user WHERE role != 'system-admin'"
    )['count']

    total_sightings = db.fetch_one(
        "SELECT COUNT(*) as count FROM sighting"
    )['count']

    # Breakdown by role
    role_counts = db.fetch_query(
        "SELECT role, COUNT(*) as count FROM user GROUP BY role"
    )
    role_map = {r['role']: r['count'] for r in role_counts}

    return render_template('system-admin-dashboard.html',
        user=user,
        total_schools=total_schools,
        total_communities=total_communities,
        total_users=total_users,
        total_sightings=total_sightings,
        role_map=role_map
    )
 
         
#Retriving community member's  data from DB and filling its dashboard        
@app.route('/dashboard/community-member')
def community_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    sighting_count = db.fetch_one(
        'SELECT COUNT(*) as count FROM sighting WHERE user_id = ?',
        (session['user_id'],)
    )['count']

    challenges_joined = db.fetch_one(
        'SELECT COUNT(*) as count FROM challenge_submission WHERE student_id = ?',
        (session['user_id'],)
    )['count']

    # Total members in their community
    community_members = db.fetch_one(
        "SELECT COUNT(*) as count FROM user WHERE organization_id = ? AND role = 'community-member'",
        (user['organization_id'],)
    )['count']

    # Sightings from whole community
    community_sightings = db.fetch_one('''
        SELECT COUNT(*) as count FROM sighting s
        JOIN user u ON s.user_id = u.user_id
        WHERE u.organization_id = ?
    ''', (user['organization_id'],))['count']

    return render_template('community-dashboard.html',
        user=user,
        sighting_count=sighting_count,
        challenges_joined=challenges_joined,
        community_members=community_members,
        community_sightings=community_sightings
    )


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

    species_count = db.fetch_one('SELECT COUNT(*) as count FROM species')['count']
    sighting_count = db.fetch_one('SELECT COUNT(*) as count FROM sighting')['count']
    school_count = db.fetch_one(
        "SELECT COUNT(*) as count FROM organization WHERE category = 'school'"
    )['count']
    community_member_count = db.fetch_one(
        "SELECT COUNT(*) as count FROM user WHERE role = 'community-member'"
    )['count']

    return render_template('public-dashboard.html',
        user=user,
        species_count=species_count,
        sighting_count=sighting_count,
        school_count=school_count,
        community_member_count=community_member_count
    )

#Retreiving Platform Analytics for System Admin
@app.route('/platform-analytics')
def platform_analytics():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    if user['role'] != 'system-admin':
        return redirect(url_for(f'/dashboard/{user["role"]}'))
    
    # Read which section was requested
    section = request.args.get('section', 'analytics')  # default to analytics


    # User stats
    total_users = db.fetch_one(
        "SELECT COUNT(*) as count FROM user WHERE role != 'system-admin'"
    )['count']

    role_counts = db.fetch_query(
        "SELECT role, COUNT(*) as count FROM user GROUP BY role"
    )
    role_map = {r['role']: r['count'] for r in role_counts}

    # Org stats
    total_schools = db.fetch_one(
        "SELECT COUNT(*) as count FROM organization WHERE category = 'school'"
    )['count']

    total_communities = db.fetch_one(
        "SELECT COUNT(*) as count FROM organization WHERE category = 'community'"
    )['count']

    avg_school_size = db.fetch_one('''
        SELECT ROUND(AVG(cnt), 0) as avg FROM (
            SELECT COUNT(*) as cnt FROM user
            WHERE role = 'student'
            GROUP BY organization_id
        )
    ''')['avg'] or 0

    avg_community_size = db.fetch_one('''
        SELECT ROUND(AVG(cnt), 0) as avg FROM (
            SELECT COUNT(*) as cnt FROM user
            WHERE role = 'community-member'
            GROUP BY organization_id
        )
    ''')['avg'] or 0

    # Sighting stats
    total_sightings = db.fetch_one(
        "SELECT COUNT(*) as count FROM sighting"
    )['count']

    species_count = db.fetch_one(
        "SELECT COUNT(DISTINCT species_id) as count FROM sighting"
    )['count']

    # Most active school
    most_active_school = db.fetch_one('''
        SELECT o.name, COUNT(s.sighting_id) as cnt
        FROM sighting s
        JOIN user u ON s.user_id = u.user_id
        JOIN organization o ON u.organization_id = o.organization_id
        WHERE o.category = 'school'
        GROUP BY o.organization_id
        ORDER BY cnt DESC LIMIT 1
    ''')

    # Most active community
    most_active_community = db.fetch_one('''
        SELECT o.name, COUNT(s.sighting_id) as cnt
        FROM sighting s
        JOIN user u ON s.user_id = u.user_id
        JOIN organization o ON u.organization_id = o.organization_id
        WHERE o.category = 'community'
        GROUP BY o.organization_id
        ORDER BY cnt DESC LIMIT 1
    ''')

    # Most reported species
    most_reported_species = db.fetch_one('''
        SELECT sp.common_name, COUNT(s.sighting_id) as cnt
        FROM sighting s
        JOIN species sp ON s.species_id = sp.species_id
        GROUP BY s.species_id
        ORDER BY cnt DESC LIMIT 1
    ''')

    # All organizations for manage schools/communities
    schools = db.fetch_query('''
        SELECT o.*,
            COUNT(DISTINCT CASE WHEN u.role = 'student' THEN u.user_id END) as student_count,
            COUNT(DISTINCT CASE WHEN u.role = 'teacher' THEN u.user_id END) as teacher_count,
            COUNT(DISTINCT s.sighting_id) as sighting_count,
            (SELECT user_id FROM user 
            WHERE organization_id = o.organization_id 
            AND role = 'school-admin' LIMIT 1) as admin_user_id
        FROM organization o
        LEFT JOIN user u ON u.organization_id = o.organization_id
        LEFT JOIN sighting s ON s.user_id = u.user_id
        WHERE o.category = 'school'
        GROUP BY o.organization_id
        ORDER BY o.name
    ''')

    communities = db.fetch_query('''
        SELECT o.*,
            COUNT(DISTINCT CASE WHEN u.role = 'community-member' THEN u.user_id END) as member_count,
            COUNT(DISTINCT s.sighting_id) as sighting_count,
            (SELECT user_id FROM user 
            WHERE organization_id = o.organization_id 
            AND role = 'community-admin' LIMIT 1) as admin_user_id
        FROM organization o
        LEFT JOIN user u ON u.organization_id = o.organization_id
        LEFT JOIN sighting s ON s.user_id = u.user_id
        WHERE o.category = 'community'
        GROUP BY o.organization_id
        ORDER BY o.name
    ''')

    return render_template('shared/platform-analytics.html',
        user=user,
        total_users=total_users,
        role_map=role_map,
        total_schools=total_schools,
        total_communities=total_communities,
        avg_school_size=avg_school_size,
        avg_community_size=avg_community_size,
        total_sightings=total_sightings,
        species_count=species_count,
        most_active_school=most_active_school,
        most_active_community=most_active_community,
        most_reported_species=most_reported_species,
        schools=schools,
        communities=communities,
        active_section = section
    )

#Retrieving species data to fill species library page
@app.route('/species-library')
def species_library():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ? ', (session['user_id'],))
    
    sql = 'SELECT * FROM species'
    species = db.fetch_query(sql)
    
    sightings = db.fetch_query('''
        SELECT s.sighting_id, s.count, s.location, s.region,
               s.sighting_date, s.description, s.photo,
               sp.common_name,
               o.name as org_name, o.category as org_category, o.avatar as org_avatar,
               u.organization_id as reporter_org_id
        FROM sighting s
        JOIN species sp ON s.species_id = sp.species_id
        JOIN user u ON s.user_id = u.user_id
        LEFT JOIN organization o ON u.organization_id = o.organization_id
        ORDER BY s.submitted_at DESC
    ''')

    programs_raw = db.fetch_query('''
        SELECT p.program_id, p.title, p.description, p.species_focus,
               p.duration, p.created_at,
               COUNT(DISTINCT e.student_id) as enrolled_count,
               o.name as org_name, o.category as org_category, o.avatar as org_avatar,
               u.organization_id as creator_org_id
        FROM program p
        JOIN user u ON p.created_by = u.user_id
        LEFT JOIN organization o ON u.organization_id = o.organization_id
        LEFT JOIN enrollment e ON p.program_id = e.program_id
        GROUP BY p.program_id
        ORDER BY p.created_at DESC
    ''')

    # Attach files to each program
    programs = []
    for p in programs_raw:
        files = db.fetch_query(
            'SELECT file_id, filename, filepath FROM program_file WHERE program_id = ?',
            (p['program_id'],)
        )
        programs.append({**dict(p), 'files': [dict(f) for f in files]})

    challenges = db.fetch_query('''
        SELECT c.challenge_id, c.title, c.description, c.points,
               c.species_focus, c.deadline, c.created_at,
               CASE WHEN c.deadline < datetime('now') THEN 'expired' ELSE 'active' END as status,
               COUNT(DISTINCT cs.submission_id) as submission_count,
               o.name as org_name, o.category as org_category, o.avatar as org_avatar,
               u.organization_id as creator_org_id
        FROM challenge c
        JOIN user u ON c.created_by = u.user_id
        LEFT JOIN organization o ON u.organization_id = o.organization_id
        LEFT JOIN challenge_submission cs ON c.challenge_id = cs.challenge_id
        GROUP BY c.challenge_id
        ORDER BY c.created_at DESC
    ''')
    
    return render_template("shared/species-library.html",
        user=user, species=species,
        sightings=[dict(s) for s in sightings],
        programs=programs,
        challenges=[dict(c) for c in challenges]
    )
    
    
# ===== CLASSES =====
# Getting classes details
@app.route('/classes')
def get_classes():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] not in ['school-admin', 'principal', 'teacher']:
        return abort(403)

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    org_id = session.get('organization_id')

    # Fetch all classes with teacher name and student count
    if session['role'] == 'teacher':
        sql = '''
            SELECT c.*,
                u.fullname as teacher_name,
                (SELECT COUNT(*) FROM class_enrollment ce
                WHERE ce.class_id = c.class_id) as student_count
            FROM class c
            LEFT JOIN user u ON c.teacher_id = u.user_id
            WHERE c.organization_id = ? AND c.teacher_id = ?
            ORDER BY c.created_at DESC
        '''
        classes = db.fetch_query(sql, (org_id, session['user_id']))
    else:
        sql = '''
            SELECT c.*,
                u.fullname as teacher_name,
                (SELECT COUNT(*) FROM class_enrollment ce
                WHERE ce.class_id = c.class_id) as student_count
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
    if session['role'] not in ['school-admin', 'principal', 'teacher']:
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

# ============================================================
# CLASS SUBMISSIONS — reuses shared/student-submissions.html
# Route: /class-submissions/<class_id>
# ============================================================

@app.route('/class-submissions/<int:class_id>')
def class_submissions(class_id):
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return abort(403)

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    class_ = db.fetch_one(
        'SELECT * FROM class WHERE class_id = ? AND organization_id = ?',
        (class_id, session['organization_id'])
    )
    if not class_:
        return abort(404)

    # All students enrolled in this class
    students = db.fetch_query('''
        SELECT u.user_id
        FROM class_enrollment ce
        JOIN user u ON ce.student_id = u.user_id
        WHERE ce.class_id = ?
    ''', (class_id,))

    student_ids = [s['user_id'] for s in students]

    if not student_ids:
        return render_template('shared/student-submissions.html',
            user=user,
            student={'fullname': class_['name'], 'email': f'{len(student_ids)} students', 'user_id': None, 'points': 0},
            programs=[], challenges=[], sightings=[], creative_files=[],
            view_mode='class', class_=dict(class_)
        )

    placeholders = ','.join('?' * len(student_ids))

    programs = db.fetch_query(f'''
        SELECT p.program_id, p.title, p.species_focus, e.status, e.enrolled_at, e.completed_at,
               e.student_id,
               u.fullname AS student_name,
               (SELECT COUNT(*) FROM program_file pf WHERE pf.program_id = p.program_id) AS total_files,
               (SELECT COUNT(*) FROM file_progress fp
                JOIN program_file pf ON fp.file_id = pf.file_id
                WHERE pf.program_id = p.program_id AND fp.student_id = e.student_id) AS done_files,
               sa.score AS teacher_score, sa.feedback AS teacher_feedback,
               sa.assessed_at, u2.fullname AS assessor_name
        FROM enrollment e
        JOIN program p ON e.program_id = p.program_id
        JOIN user u ON e.student_id = u.user_id
        LEFT JOIN student_assessment sa
               ON sa.student_id = e.student_id AND sa.subject_type = 'program' AND sa.subject_id = p.program_id
        LEFT JOIN user u2 ON sa.assessor_id = u2.user_id
        WHERE e.student_id IN ({placeholders})
        ORDER BY u.fullname ASC, e.enrolled_at DESC
    ''', student_ids)

    challenges = db.fetch_query(f'''
        SELECT c.challenge_id, c.title AS challenge_title, c.points, c.species_focus,
               cs.submission_id, cs.student_id, cs.submitted_at,
               cs.description AS submission_note, cs.media_path,
               u.fullname AS student_name,
               ag.score, ag.feedback, ag.graded_at, u2.fullname AS grader_name
        FROM challenge_submission cs
        JOIN challenge c ON cs.challenge_id = c.challenge_id
        JOIN user u ON cs.student_id = u.user_id
        LEFT JOIN assessment_grade ag ON ag.submission_id = cs.submission_id
        LEFT JOIN user u2 ON ag.graded_by = u2.user_id
        WHERE cs.student_id IN ({placeholders}) AND c.organization_id = ?
        ORDER BY u.fullname ASC, cs.submitted_at DESC
    ''', student_ids + [session['organization_id']])

    sightings = db.fetch_query(f'''
        SELECT s.*, sp.common_name,
               u.fullname AS student_name,
               sa.score AS teacher_score, sa.feedback AS teacher_feedback,
               sa.assessed_at, u2.fullname AS assessor_name
        FROM sighting s
        JOIN species sp ON s.species_id = sp.species_id
        JOIN user u ON s.user_id = u.user_id
        LEFT JOIN student_assessment sa
               ON sa.student_id = s.user_id AND sa.subject_type = 'sighting' AND sa.subject_id = s.sighting_id
        LEFT JOIN user u2 ON sa.assessor_id = u2.user_id
        WHERE s.user_id IN ({placeholders})
        ORDER BY u.fullname ASC, s.submitted_at DESC
    ''', student_ids)

    creative_files = db.fetch_query(f'''
        SELECT cf.*,
               u.fullname AS student_name,
               sa.score AS teacher_score, sa.feedback AS teacher_feedback,
               sa.assessed_at, u2.fullname AS assessor_name
        FROM creative_file cf
        JOIN user u ON cf.user_id = u.user_id
        LEFT JOIN student_assessment sa
               ON sa.student_id = cf.user_id AND sa.subject_type = 'creative_file' AND sa.subject_id = cf.file_id
        LEFT JOIN user u2 ON sa.assessor_id = u2.user_id
        WHERE cf.user_id IN ({placeholders})
        ORDER BY u.fullname ASC, cf.uploaded_at DESC
    ''', student_ids)

    return render_template('shared/student-submissions.html',
        user=user,
        student={'fullname': class_['name'], 'email': f'{len(student_ids)} students', 'user_id': None, 'points': 0},
        programs=[dict(p) for p in programs],
        challenges=[dict(c) for c in challenges],
        sightings=[dict(s) for s in sightings],
        creative_files=[dict(f) for f in creative_files],
        view_mode='class',
        class_=dict(class_)
    )



#Get all Submissions made by a student
@app.route('/student-submissions/<int:student_id>')
def student_submissions(student_id):
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return abort(403)

    user    = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    student = db.fetch_one(
        'SELECT * FROM user WHERE user_id = ? AND organization_id = ?',
        (student_id, session['organization_id'])
    )
    if not student:
        return abort(404)

    # Programs with assessment
    programs = db.fetch_query('''
        SELECT p.program_id, p.title, p.species_focus, e.status, e.enrolled_at, e.completed_at,
               (SELECT COUNT(*) FROM program_file pf WHERE pf.program_id = p.program_id) as total_files,
               (SELECT COUNT(*) FROM file_progress fp
                JOIN program_file pf ON fp.file_id = pf.file_id
                WHERE pf.program_id = p.program_id AND fp.student_id = ?) as done_files,
               sa.score as teacher_score, sa.feedback as teacher_feedback,
               sa.assessed_at, u.fullname as assessor_name
        FROM enrollment e
        JOIN program p ON e.program_id = p.program_id
        LEFT JOIN student_assessment sa
               ON sa.student_id = ? AND sa.subject_type = 'program' AND sa.subject_id = p.program_id
        LEFT JOIN user u ON sa.assessor_id = u.user_id
        WHERE e.student_id = ?
        ORDER BY e.enrolled_at DESC
    ''', (student_id, student_id, student_id))

    # Challenges with grades
    challenges = db.fetch_query('''
        SELECT c.challenge_id, c.title as challenge_title, c.points, c.species_focus,
               cs.submission_id, cs.submitted_at, cs.description as submission_note, cs.media_path,
               ag.score, ag.feedback, ag.graded_at, gr.fullname as grader_name
        FROM challenge_submission cs
        JOIN challenge c ON cs.challenge_id = c.challenge_id
        LEFT JOIN assessment_grade ag ON ag.submission_id = cs.submission_id
        LEFT JOIN user gr ON ag.graded_by = gr.user_id
        WHERE cs.student_id = ? AND c.organization_id = ?
        ORDER BY cs.submitted_at DESC
    ''', (student_id, session['organization_id']))

    # Sightings with assessment
    sightings = db.fetch_query('''
        SELECT s.*, sp.common_name,
               sa.score as teacher_score, sa.feedback as teacher_feedback,
               sa.assessed_at, u.fullname as assessor_name
        FROM sighting s
        JOIN species sp ON s.species_id = sp.species_id
        LEFT JOIN student_assessment sa
               ON sa.student_id = ? AND sa.subject_type = 'sighting' AND sa.subject_id = s.sighting_id
        LEFT JOIN user u ON sa.assessor_id = u.user_id
        WHERE s.user_id = ?
        ORDER BY s.submitted_at DESC
    ''', (student_id, student_id))

    # Creative files with assessment
    creative_files = db.fetch_query('''
        SELECT cf.*,
               sa.score as teacher_score, sa.feedback as teacher_feedback,
               sa.assessed_at, u.fullname as assessor_name
        FROM creative_file cf
        LEFT JOIN student_assessment sa
               ON sa.student_id = ? AND sa.subject_type = 'creative_file' AND sa.subject_id = cf.file_id
        LEFT JOIN user u ON sa.assessor_id = u.user_id
        WHERE cf.user_id = ?
        ORDER BY cf.uploaded_at DESC
    ''', (student_id, student_id))

    return render_template('shared/student-submissions.html',
        user=user,
        student=dict(student),
        programs=[dict(p) for p in programs],
        challenges=[dict(c) for c in challenges],
        sightings=[dict(s) for s in sightings],
        creative_files=[dict(f) for f in creative_files]
    )

#Retreive all the submissions for library   
@app.route('/public-challenge-submissions/<int:challenge_id>')
def public_challenge_submissions(challenge_id):
    if 'user_id' not in session:
        return redirect(url_for('login_get'))

    challenge = db.fetch_one(
        'SELECT * FROM challenge WHERE challenge_id = ?', (challenge_id,)
    )
    if not challenge:
        return abort(404)

    submissions = db.fetch_query('''
        SELECT cs.submission_id, cs.submitted_at, cs.description, cs.media_path,
               o.name as org_name, o.category as org_category, o.avatar as org_avatar,
               ag.score, ag.feedback
        FROM challenge_submission cs
        JOIN user u ON cs.student_id = u.user_id
        LEFT JOIN organization o ON u.organization_id = o.organization_id
        LEFT JOIN assessment_grade ag ON ag.submission_id = cs.submission_id
        WHERE cs.challenge_id = ?
        ORDER BY cs.submitted_at DESC
    ''', (challenge_id,))

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    return render_template('shared/public-challenge-submissions.html',
        user=user,
        challenge=dict(challenge),
        submissions=[dict(s) for s in submissions]
    )

# Assessment + Student Progress Report
# Route: teacher views all submissions for a challenge and can grade them
@app.route('/assess-submissions/<int:challenge_id>')
def assess_submissions(challenge_id):
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] not in ['teacher', 'school-admin', 'principal', 'community-admin']:
        return abort(403)

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    
    if user['role'] not in ['teacher', 'community-admin', 'school-admin', 'principal']:
        return redirect('/dashboard')

    challenge = db.fetch_one(
        'SELECT * FROM challenge WHERE challenge_id = ? AND organization_id = ?',
        (challenge_id, session['organization_id'])
    )
    if not challenge:
        return abort(404)

    submissions = db.fetch_query('''
        SELECT cs.*,
               u.fullname as student_name, u.avatar as student_avatar, u.role as student_role,
               ag.score, ag.feedback, ag.graded_at, ag.graded_by,
               gr.fullname as grader_name
        FROM challenge_submission cs
        JOIN user u ON cs.student_id = u.user_id
        LEFT JOIN assessment_grade ag ON ag.submission_id = cs.submission_id
        LEFT JOIN user gr ON ag.graded_by = gr.user_id
        WHERE cs.challenge_id = ?
        ORDER BY cs.submitted_at DESC
    ''', (challenge_id,))

    return render_template('shared/assess-submissions.html',
        user=user,
        challenge=dict(challenge),
        submissions=[dict(s) for s in submissions]
    )


# Route: save a grade/feedback on a submission
@app.route('/grade-submission/<int:submission_id>', methods=['POST'])
def grade_submission(submission_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['teacher', 'school-admin', 'principal', 'community-admin']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data     = request.get_json()
    score    = data.get('score')
    feedback = data.get('feedback', '').strip()

    # Validate score
    if score is not None:
        try:
            score = int(score)
            if not (0 <= score <= 100):
                return jsonify({'success': False, 'message': 'Score must be 0–100'})
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid score'})

    # Upsert: update if exists, insert if not
    existing = db.fetch_one(
        'SELECT grade_id FROM assessment_grade WHERE submission_id = ?', (submission_id,)
    )
    if existing:
        db.execute_query(
            '''UPDATE assessment_grade
               SET score = ?, feedback = ?, graded_by = ?, graded_at = CURRENT_TIMESTAMP
               WHERE submission_id = ?''',
            (score, feedback or None, session['user_id'], submission_id)
        )
    else:
        db.execute_query(
            '''INSERT INTO assessment_grade (submission_id, score, feedback, graded_by)
               VALUES (?, ?, ?, ?)''',
            (submission_id, score, feedback or None, session['user_id'])
        )

    return jsonify({'success': True})

# Generic assessment route for programs, sightings, creative files
@app.route('/assess-student/<int:student_id>', methods=['POST'])
def assess_student(student_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data         = request.get_json()
    subject_type = data.get('subject_type')  # 'program' | 'sighting' | 'creative_file'
    subject_id   = data.get('subject_id')
    score        = data.get('score')
    feedback     = data.get('feedback', '').strip()

    if subject_type not in ['program', 'sighting', 'creative_file']:
        return jsonify({'success': False, 'message': 'Invalid subject type'})

    if score is not None:
        try:
            score = int(score)
            if not (0 <= score <= 100):
                return jsonify({'success': False, 'message': 'Score must be 0–100'})
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid score'})

    existing = db.fetch_one(
        '''SELECT assessment_id FROM student_assessment
           WHERE student_id = ? AND subject_type = ? AND subject_id = ?''',
        (student_id, subject_type, subject_id)
    )
    if existing:
        db.execute_query(
            '''UPDATE student_assessment
               SET score = ?, feedback = ?, assessor_id = ?, assessed_at = CURRENT_TIMESTAMP
               WHERE student_id = ? AND subject_type = ? AND subject_id = ?''',
            (score, feedback or None, session['user_id'], student_id, subject_type, subject_id)
        )
    else:
        db.execute_query(
            '''INSERT INTO student_assessment
               (student_id, assessor_id, subject_type, subject_id, score, feedback)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (student_id, session['user_id'], subject_type, subject_id, score, feedback or None)
        )

    assessor = db.fetch_one('SELECT fullname FROM user WHERE user_id = ?', (session['user_id'],))
    return jsonify({'success': True, 'assessor_name': assessor['fullname']})

#Retrieving student's submission data
@app.route('/my-submissions')
def my_submissions():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] != 'student':
        return abort(403)

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    programs = db.fetch_query('''
        SELECT p.program_id, p.title, p.species_focus, e.status, e.enrolled_at, e.completed_at,
               (SELECT COUNT(*) FROM program_file pf WHERE pf.program_id = p.program_id) as total_files,
               (SELECT COUNT(*) FROM file_progress fp
                JOIN program_file pf ON fp.file_id = pf.file_id
                WHERE pf.program_id = p.program_id AND fp.student_id = ?) as done_files,
               sa.score as teacher_score, sa.feedback as teacher_feedback,
               sa.assessed_at, u.fullname as assessor_name
        FROM enrollment e
        JOIN program p ON e.program_id = p.program_id
        LEFT JOIN student_assessment sa
               ON sa.student_id = ? AND sa.subject_type = 'program' AND sa.subject_id = p.program_id
        LEFT JOIN user u ON sa.assessor_id = u.user_id
        WHERE e.student_id = ?
        ORDER BY e.enrolled_at DESC
    ''', (session['user_id'], session['user_id'], session['user_id']))

    challenges = db.fetch_query('''
        SELECT c.challenge_id, c.title as challenge_title, c.points, c.species_focus,
               cs.submission_id, cs.submitted_at, cs.description as submission_note, cs.media_path,
               ag.score, ag.feedback, ag.graded_at, gr.fullname as grader_name
        FROM challenge_submission cs
        JOIN challenge c ON cs.challenge_id = c.challenge_id
        LEFT JOIN assessment_grade ag ON ag.submission_id = cs.submission_id
        LEFT JOIN user gr ON ag.graded_by = gr.user_id
        WHERE cs.student_id = ?
        ORDER BY cs.submitted_at DESC
    ''', (session['user_id'],))

    sightings = db.fetch_query('''
        SELECT s.*, sp.common_name,
               sa.score as teacher_score, sa.feedback as teacher_feedback,
               sa.assessed_at, u.fullname as assessor_name
        FROM sighting s
        JOIN species sp ON s.species_id = sp.species_id
        LEFT JOIN student_assessment sa
               ON sa.student_id = ? AND sa.subject_type = 'sighting' AND sa.subject_id = s.sighting_id
        LEFT JOIN user u ON sa.assessor_id = u.user_id
        WHERE s.user_id = ?
        ORDER BY s.submitted_at DESC
    ''', (session['user_id'], session['user_id']))

    creative_files = db.fetch_query('''
        SELECT cf.*,
               sa.score as teacher_score, sa.feedback as teacher_feedback,
               sa.assessed_at, u.fullname as assessor_name
        FROM creative_file cf
        LEFT JOIN student_assessment sa
               ON sa.student_id = ? AND sa.subject_type = 'creative_file' AND sa.subject_id = cf.file_id
        LEFT JOIN user u ON sa.assessor_id = u.user_id
        WHERE cf.user_id = ?
        ORDER BY cf.uploaded_at DESC
    ''', (session['user_id'], session['user_id']))

    # Pass student object same as teacher route expects
    return render_template('shared/student-submissions.html',
        user=user,
        student=dict(user),  # student is viewing their own page
        programs=[dict(p) for p in programs],
        challenges=[dict(c) for c in challenges],
        sightings=[dict(s) for s in sightings],
        creative_files=[dict(f) for f in creative_files]
    )


# Student Progress Report
@app.route('/student-progress/<int:student_id>')
def student_progress(student_id):
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] not in ['teacher', 'school-admin', 'principal', 'student']:
        return abort(403)

    # Students can only view their own progress
    if session['role'] == 'student' and session['user_id'] != student_id:
        return abort(403)

    user    = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    student = db.fetch_one(
        'SELECT * FROM user WHERE user_id = ? AND organization_id = ?',
        (student_id, session['organization_id'])
    )
    if not student:
        return abort(404)

    # ── Syllabus progress: all classes the student is enrolled in ──
    classes = db.fetch_query('''
        SELECT c.class_id, c.name, c.subject,
               u.fullname as teacher_name
        FROM class_enrollment ce
        JOIN class c ON ce.class_id = c.class_id
        LEFT JOIN user u ON c.teacher_id = u.user_id
        WHERE ce.student_id = ?
    ''', (student_id,))

    classes_progress = []
    for cls in classes:
        topics = db.fetch_query(
            'SELECT * FROM syllabus_topic WHERE class_id = ? ORDER BY order_index ASC',
            (cls['class_id'],)
        )
        topics_data = []
        total_acts = 0
        done_acts  = 0
        for t in topics:
            activities = db.fetch_query('''
                SELECT sa.*,
                       CASE WHEN sac.completion_id IS NOT NULL THEN 1 ELSE 0 END AS is_completed
                FROM syllabus_activity sa
                LEFT JOIN syllabus_activity_completion sac
                       ON sac.activity_id = sa.activity_id AND sac.student_id = ?
                WHERE sa.topic_id = ?
                ORDER BY sa.order_index ASC
            ''', (student_id, t['topic_id']))
            acts      = [dict(a) for a in activities]
            t_done    = sum(1 for a in acts if a['is_completed'])
            total_acts += len(acts)
            done_acts  += t_done
            topics_data.append({**dict(t), 'activities': acts,
                                 'done': t_done, 'total': len(acts)})
        pct = round(done_acts / total_acts * 100) if total_acts else 0
        classes_progress.append({**dict(cls), 'topics': topics_data,
                                  'done': done_acts, 'total': total_acts, 'pct': pct})

    # ── Program enrollments ──
    programs = db.fetch_query('''
        SELECT p.title, p.species_focus, e.status, e.enrolled_at, e.completed_at,
               (SELECT COUNT(*) FROM program_file pf WHERE pf.program_id = p.program_id) as total_files,
               (SELECT COUNT(*) FROM file_progress fp
                JOIN program_file pf ON fp.file_id = pf.file_id
                WHERE pf.program_id = p.program_id AND fp.student_id = ?) as done_files
        FROM enrollment e
        JOIN program p ON e.program_id = p.program_id
        WHERE e.student_id = ?
        ORDER BY e.enrolled_at DESC
    ''', (student_id, student_id))

    # ── Challenge submissions with grades ──
    submissions = db.fetch_query('''
        SELECT c.title as challenge_title, c.points, c.species_focus,
               cs.submitted_at, cs.description as submission_note, cs.media_path,
               ag.score, ag.feedback, ag.graded_at
        FROM challenge_submission cs
        JOIN challenge c ON cs.challenge_id = c.challenge_id
        LEFT JOIN assessment_grade ag ON ag.submission_id = cs.submission_id
        WHERE cs.student_id = ? AND c.organization_id = ?
        ORDER BY cs.submitted_at DESC
    ''', (student_id, session['organization_id']))

    # ── Sightings ──
    sightings = db.fetch_query('''
        SELECT s.sighting_date, s.location, s.count, sp.common_name
        FROM sighting s
        JOIN species sp ON s.species_id = sp.species_id
        WHERE s.user_id = ?
        ORDER BY s.submitted_at DESC
    ''', (student_id,))

    return render_template('shared/student-progress.html',
        user=user,
        student=dict(student),
        classes_progress=classes_progress,
        programs=[dict(p) for p in programs],
        submissions=[dict(s) for s in submissions],
        sightings=[dict(s) for s in sightings]
    )


# GET: render notes page (class-wide announcements + private student notes)
@app.route('/notes/<int:class_id>')
def get_notes(class_id):
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return abort(403)

    # Ownership check
    if session['role'] == 'teacher':
        cls = db.fetch_one(
            'SELECT * FROM class WHERE class_id = ? AND teacher_id = ?',
            (class_id, session['user_id'])
        )
    else:
        cls = db.fetch_one(
            'SELECT * FROM class WHERE class_id = ? AND organization_id = ?',
            (class_id, session['organization_id'])
        )
    if not cls:
        return abort(404)

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    # Class-wide announcements (target_student_id IS NULL)
    announcements = db.fetch_query('''
        SELECT n.*, u.fullname as author_name
        FROM note n
        JOIN user u ON n.created_by = u.user_id
        WHERE n.class_id = ? AND n.target_student_id IS NULL
        ORDER BY n.created_at DESC
    ''', (class_id,))

    # Students in class with their private notes
    students = db.fetch_query('''
        SELECT u.user_id, u.fullname, u.avatar
        FROM class_enrollment ce
        JOIN user u ON ce.student_id = u.user_id
        WHERE ce.class_id = ?
        ORDER BY u.fullname
    ''', (class_id,))

    students_with_notes = []
    for s in students:
        notes = db.fetch_query('''
            SELECT n.*, u.fullname as author_name
            FROM note n
            JOIN user u ON n.created_by = u.user_id
            WHERE n.class_id = ? AND n.target_student_id = ?
            ORDER BY n.created_at DESC
        ''', (class_id, s['user_id']))
        students_with_notes.append({**dict(s), 'notes': [dict(n) for n in notes]})

    return render_template('shared/notes.html',
        user=user,
        cls=dict(cls),
        announcements=[dict(a) for a in announcements],
        students=students_with_notes
    )


# POST: create a note
@app.route('/notes/<int:class_id>/create', methods=['POST'])
def create_note(class_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data              = request.get_json()
    body              = data.get('body', '').strip()
    target_student_id = data.get('target_student_id') or None  # None = class-wide
    note_type         = data.get('note_type', 'announcement')   # 'announcement' | 'private'

    if not body:
        return jsonify({'success': False, 'message': 'Note body is required'})

    db.execute_query(
        '''INSERT INTO note (class_id, created_by, target_student_id, body, note_type)
           VALUES (?, ?, ?, ?, ?)''',
        (class_id, session['user_id'], target_student_id, body, note_type)
    )
    new = db.fetch_one(
        'SELECT * FROM note WHERE class_id = ? ORDER BY note_id DESC LIMIT 1',
        (class_id,)
    )
    return jsonify({'success': True, 'note': dict(new)})


# POST: delete a note
@app.route('/notes/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    note = db.fetch_one('SELECT * FROM note WHERE note_id = ?', (note_id,))
    if not note:
        return jsonify({'success': False, 'message': 'Note not found'})

    # Only author or admin can delete
    if note['created_by'] != session['user_id'] and session['role'] not in ['school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    db.execute_query('DELETE FROM note WHERE note_id = ?', (note_id,))
    return jsonify({'success': True})


# Student: view notes/announcements for their class
@app.route('/my-notes/<int:class_id>')
def student_notes(class_id):
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] != 'student':
        return abort(403)

    enrolled = db.fetch_one(
        'SELECT * FROM class_enrollment WHERE class_id = ? AND student_id = ?',
        (class_id, session['user_id'])
    )
    if not enrolled:
        return abort(403)

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    cls  = db.fetch_one('SELECT * FROM class WHERE class_id = ?', (class_id,))

    announcements = db.fetch_query('''
        SELECT n.*, u.fullname as author_name
        FROM note n
        JOIN user u ON n.created_by = u.user_id
        WHERE n.class_id = ? AND n.target_student_id IS NULL
        ORDER BY n.created_at DESC
    ''', (class_id,))

    private_notes = db.fetch_query('''
        SELECT n.*, u.fullname as author_name
        FROM note n
        JOIN user u ON n.created_by = u.user_id
        WHERE n.class_id = ? AND n.target_student_id = ?
        ORDER BY n.created_at DESC
    ''', (class_id, session['user_id']))

    # Fetch teacher
    teacher = db.fetch_one(
        'SELECT user_id, fullname, avatar FROM user WHERE user_id = ?',
        (cls['teacher_id'],)
    ) if cls['teacher_id'] else None

    # Fetch classmates (excluding self)
    classmates = db.fetch_query('''
        SELECT u.user_id, u.fullname, u.avatar
        FROM class_enrollment ce
        JOIN user u ON ce.student_id = u.user_id
        WHERE ce.class_id = ? AND ce.student_id != ?
        ORDER BY u.fullname
    ''', (class_id, session['user_id']))

    return render_template('shared/student-notes.html',
        user=user,
        cls=dict(cls),
        announcements=[dict(a) for a in announcements],
        private_notes=[dict(n) for n in private_notes],
        teacher=dict(teacher) if teacher else None,
        classmates=[dict(c) for c in classmates]
    )

# Sightings filtered by class
@app.route('/class-sightings/<int:class_id>')
def class_sightings(class_id):
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return abort(403)

    # Ownership check
    if session['role'] == 'teacher':
        cls = db.fetch_one(
            'SELECT * FROM class WHERE class_id = ? AND teacher_id = ?',
            (class_id, session['user_id'])
        )
    else:
        cls = db.fetch_one(
            'SELECT * FROM class WHERE class_id = ? AND organization_id = ?',
            (class_id, session['organization_id'])
        )
    if not cls:
        return abort(404)

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    sightings = db.fetch_query('''
        SELECT s.*, sp.common_name, sp.species_id as sp_id,
               u.fullname as reporter_name, u.role as reporter_role,
               u.avatar as reporter_avatar
        FROM sighting s
        JOIN species sp ON s.species_id = sp.species_id
        JOIN user u ON s.user_id = u.user_id
        JOIN class_enrollment ce ON ce.student_id = u.user_id AND ce.class_id = ?
        ORDER BY s.submitted_at DESC
    ''', (class_id,))

    return render_template('shared/class-sightings.html',
        user=user,
        cls=dict(cls),
        sightings=[dict(s) for s in sightings]
    )


# Edit an activity
@app.route('/syllabus/activity/<int:activity_id>/edit', methods=['POST'])
def edit_activity(activity_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    # Ownership: activity → topic → class
    activity = db.fetch_one(
        'SELECT topic_id FROM syllabus_activity WHERE activity_id = ?', (activity_id,)
    )
    if not activity:
        return jsonify({'success': False, 'message': 'Activity not found'})
    topic = db.fetch_one(
        'SELECT class_id FROM syllabus_topic WHERE topic_id = ?', (activity['topic_id'],)
    )
    if session['role'] == 'teacher':
        cls = db.fetch_one(
            'SELECT class_id FROM class WHERE class_id = ? AND teacher_id = ?',
            (topic['class_id'], session['user_id'])
        )
    else:
        cls = db.fetch_one(
            'SELECT class_id FROM class WHERE class_id = ? AND organization_id = ?',
            (topic['class_id'], session['organization_id'])
        )
    if not cls:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data          = request.get_json()
    title         = data.get('title', '').strip()
    desc          = data.get('description', '').strip()
    activity_type = data.get('activity_type', 'task').strip()
    program_id    = data.get('linked_program_id') or None
    challenge_id  = data.get('linked_challenge_id') or None
    species_id = data.get('linked_species_id') or None

    if not title:
        return jsonify({'success': False, 'message': 'Title is required'})

    db.execute_query(
        '''UPDATE syllabus_activity
        SET title = ?, description = ?, activity_type = ?,
            linked_program_id = ?, linked_challenge_id = ?, linked_species_id = ?
        WHERE activity_id = ?''',
        (title, desc or None, activity_type, program_id, challenge_id, species_id, activity_id)
    )

    updated = db.fetch_one('''
        SELECT sa.*, p.title AS program_title, c.title AS challenge_title
        FROM syllabus_activity sa
        LEFT JOIN program   p ON sa.linked_program_id   = p.program_id
        LEFT JOIN challenge c ON sa.linked_challenge_id = c.challenge_id
        WHERE sa.activity_id = ?
    ''', (activity_id,))

    return jsonify({'success': True, 'activity': dict(updated)})


@app.route('/programs')
def get_programs():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    user   = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    org_id = session.get('organization_id')

    programs = db.fetch_query('''
        SELECT p.*,
            u.fullname as creator_name,
            COUNT(DISTINCT e.student_id) as enrolled_count,
            COUNT(DISTINCT CASE WHEN e.status = 'doing' THEN e.student_id END) as doing_count,
            COUNT(DISTINCT CASE WHEN e.status = 'completed' THEN e.student_id END) as completed_count,
            MAX(CASE WHEN e.student_id = ? THEN 1 ELSE 0 END) as is_enrolled,
            MAX(CASE WHEN sa.linked_program_id IS NOT NULL THEN 1 ELSE 0 END) as is_recommended
        FROM program p
        JOIN user u ON p.created_by = u.user_id
        LEFT JOIN enrollment e ON p.program_id = e.program_id
        LEFT JOIN syllabus_activity sa ON sa.linked_program_id = p.program_id
            AND sa.topic_id IN (
                SELECT st.topic_id FROM syllabus_topic st
                JOIN class c ON st.class_id = c.class_id
                JOIN class_enrollment ce ON ce.class_id = c.class_id
                WHERE ce.student_id = ?
            )
        GROUP BY p.program_id
        ORDER BY is_recommended DESC, p.created_at DESC
    ''', (session['user_id'], session['user_id']))

    programs_with_files = []
    for p in programs:
        files = db.fetch_query('SELECT * FROM program_file WHERE program_id = ?', (p['program_id'],))
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

        # ── fetch linked classes INSIDE the loop for each program ──
        linked_classes = []
        if session['role'] == 'teacher':
            rows = db.fetch_query('''
                SELECT DISTINCT c.name as class_name
                FROM syllabus_activity sa
                JOIN syllabus_topic st ON sa.topic_id = st.topic_id
                JOIN class c ON st.class_id = c.class_id
                WHERE sa.linked_program_id = ?
                AND c.organization_id = ?
            ''', (p['program_id'], org_id))
            linked_classes = [r['class_name'] for r in rows]

        # single append with everything
        programs_with_files.append({
            **dict(p),
            'files': files_with_progress,
            'linked_classes': linked_classes
        })

    species = db.fetch_query('SELECT common_name FROM species ORDER BY common_name')
    return render_template('shared/programs.html', user=user,
        programs=programs_with_files, species=species)

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
        # Auto-complete any syllabus activities linked to this program
        auto_complete_syllabus_activity(session['user_id'], 'program', program['program_id'])

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
        # Also remove syllabus activity completions linked to this program
        db.execute_query(
            '''DELETE FROM syllabus_activity_completion
            WHERE student_id = ?
            AND activity_id IN (
                SELECT activity_id FROM syllabus_activity
                WHERE activity_type = 'program' AND linked_program_id = ?
            )''',
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

# ============================================================
# SYLLABUS ROUTES 
# ============================================================

# ── Render the syllabus page for a class ────────────────────
@app.route('/syllabus/<int:class_id>')
def get_syllabus(class_id):
    if 'user_id' not in session:
        return redirect(url_for('login_get'))

    # Teachers see only their own class; admins see any class in their org
    if session['role'] == 'teacher':
        cls = db.fetch_one(
            'SELECT * FROM class WHERE class_id = ? AND teacher_id = ?',
            (class_id, session['user_id'])
        )
    elif session['role'] in ['school-admin', 'principal']:
        cls = db.fetch_one(
            'SELECT * FROM class WHERE class_id = ? AND organization_id = ?',
            (class_id, session['organization_id'])
        )
    else:
        return abort(403)

    if not cls:
        return abort(404)

    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    # Fetch topics ordered
    topics = db.fetch_query(
        'SELECT * FROM syllabus_topic WHERE class_id = ? ORDER BY order_index ASC, created_at ASC',
        (class_id,)
    )

    # Fetch activities for each topic + linked names
    topics_with_activities = []
    for t in topics:
        activities = db.fetch_query('''
            SELECT sa.*,
                   p.title  AS program_title,
                   c.title  AS challenge_title
            FROM syllabus_activity sa
            LEFT JOIN program   p ON sa.linked_program_id   = p.program_id
            LEFT JOIN challenge c ON sa.linked_challenge_id = c.challenge_id
            WHERE sa.topic_id = ?
            ORDER BY sa.order_index ASC, sa.created_at ASC
        ''', (t['topic_id'],))
        topics_with_activities.append({**dict(t), 'activities': [dict(a) for a in activities]})

    # Programs and challenges for the link-activity dropdown
    programs = db.fetch_query(
        'SELECT program_id, title FROM program WHERE organization_id = ? ORDER BY title',
        (session['organization_id'],)
    )
    challenges = db.fetch_query(
        'SELECT challenge_id, title FROM challenge WHERE organization_id = ? ORDER BY title',
        (session['organization_id'],)
    )

    species = db.fetch_query(
        'SELECT species_id, common_name FROM species ORDER BY common_name',
    )
    
    return render_template('shared/syllabus.html',
        user=user,
        cls=dict(cls),
        topics=topics_with_activities,
        programs=programs,
        challenges=challenges,
        species = species
    )


# ── Create a topic ───────────────────────────────────────────
@app.route('/syllabus/<int:class_id>/create-topic', methods=['POST'])
def create_topic(class_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    # Ownership check
    if session['role'] == 'teacher':
        cls = db.fetch_one(
            'SELECT class_id FROM class WHERE class_id = ? AND teacher_id = ?',
            (class_id, session['user_id'])
        )
    else:
        cls = db.fetch_one(
            'SELECT class_id FROM class WHERE class_id = ? AND organization_id = ?',
            (class_id, session['organization_id'])
        )
    if not cls:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data = request.get_json()
    title     = data.get('title', '').strip()
    desc      = data.get('description', '').strip()
    objective = data.get('learning_objective', '').strip()

    if not title:
        return jsonify({'success': False, 'message': 'Title is required'})

    # Next order index
    last = db.fetch_one(
        'SELECT MAX(order_index) as mx FROM syllabus_topic WHERE class_id = ?', (class_id,)
    )
    order_index = (last['mx'] or 0) + 1

    db.execute_query(
        '''INSERT INTO syllabus_topic (class_id, title, description, learning_objective, order_index)
           VALUES (?, ?, ?, ?, ?)''',
        (class_id, title, desc or None, objective or None, order_index)
    )
    new = db.fetch_one(
        'SELECT * FROM syllabus_topic WHERE class_id = ? ORDER BY topic_id DESC LIMIT 1',
        (class_id,)
    )
    return jsonify({'success': True, 'topic': dict(new)})


# ── Edit a topic ─────────────────────────────────────────────
@app.route('/syllabus/topic/<int:topic_id>/edit', methods=['POST'])
def edit_topic(topic_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    # Ownership check
    topic = db.fetch_one('SELECT class_id FROM syllabus_topic WHERE topic_id = ?', (topic_id,))
    if not topic:
        return jsonify({'success': False, 'message': 'Topic not found'})

    if session['role'] == 'teacher':
        cls = db.fetch_one(
            'SELECT class_id FROM class WHERE class_id = ? AND teacher_id = ?',
            (topic['class_id'], session['user_id'])
        )
    else:
        cls = db.fetch_one(
            'SELECT class_id FROM class WHERE class_id = ? AND organization_id = ?',
            (topic['class_id'], session['organization_id'])
        )
    if not cls:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data      = request.get_json()
    title     = data.get('title', '').strip()
    desc      = data.get('description', '').strip()
    objective = data.get('learning_objective', '').strip()

    if not title:
        return jsonify({'success': False, 'message': 'Title is required'})

    db.execute_query(
        '''UPDATE syllabus_topic
           SET title = ?, description = ?, learning_objective = ?
           WHERE topic_id = ?''',
        (title, desc or None, objective or None, topic_id)
    )
    return jsonify({'success': True})


# ── Delete a topic (cascades to its activities) ──────────────
@app.route('/syllabus/topic/<int:topic_id>/delete', methods=['POST'])
def delete_topic(topic_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    # Add ownership check
    topic = db.fetch_one('SELECT class_id FROM syllabus_topic WHERE topic_id = ?', (topic_id,))
    if not topic:
        return jsonify({'success': False, 'message': 'Topic not found'})

    if session['role'] == 'teacher':
        cls = db.fetch_one(
            'SELECT class_id FROM class WHERE class_id = ? AND teacher_id = ?',
            (topic['class_id'], session['user_id'])
        )
    else:
        cls = db.fetch_one(
            'SELECT class_id FROM class WHERE class_id = ? AND organization_id = ?',
            (topic['class_id'], session['organization_id'])
        )
    if not cls:
        return jsonify({'success': False, 'message': 'Not authorized'})

    db.execute_query('DELETE FROM syllabus_topic WHERE topic_id = ?', (topic_id,))
    return jsonify({'success': True})


# ── Reorder topics ───────────────────────────────────────────
@app.route('/syllabus/<int:class_id>/reorder-topics', methods=['POST'])
def reorder_topics(class_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    data = request.get_json()
    ordered_ids = data.get('order', [])   # list of topic_ids in new order

    for idx, tid in enumerate(ordered_ids):
        db.execute_query(
            'UPDATE syllabus_topic SET order_index = ? WHERE topic_id = ?',
            (idx + 1, tid)
        )
    return jsonify({'success': True})


# ── Create an activity inside a topic ────────────────────────
@app.route('/syllabus/topic/<int:topic_id>/create-activity', methods=['POST'])
def create_activity(topic_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    data          = request.get_json()
    title         = data.get('title', '').strip()
    desc          = data.get('description', '').strip()
    activity_type = data.get('activity_type', 'task').strip()
    program_id    = data.get('linked_program_id')   or None
    challenge_id  = data.get('linked_challenge_id') or None
    species_id = data.get('linked_species_id') or None

    if not title:
        return jsonify({'success': False, 'message': 'Title is required'})

    last = db.fetch_one(
        'SELECT MAX(order_index) as mx FROM syllabus_activity WHERE topic_id = ?', (topic_id,)
    )
    order_index = (last['mx'] or 0) + 1

    db.execute_query(
        '''INSERT INTO syllabus_activity
        (topic_id, title, description, activity_type, linked_program_id, linked_challenge_id, linked_species_id, order_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (topic_id, title, desc or None, activity_type, program_id, challenge_id, species_id, order_index)
    )
    new = db.fetch_one(
        '''SELECT sa.*, p.title AS program_title, c.title AS challenge_title
           FROM syllabus_activity sa
           LEFT JOIN program   p ON sa.linked_program_id   = p.program_id
           LEFT JOIN challenge c ON sa.linked_challenge_id = c.challenge_id
           WHERE sa.topic_id = ? ORDER BY sa.activity_id DESC LIMIT 1''',
        (topic_id,)
    )
    return jsonify({'success': True, 'activity': dict(new)})


# ── Delete an activity ───────────────────────────────────────
@app.route('/syllabus/activity/<int:activity_id>/delete', methods=['POST'])
def delete_activity(activity_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['teacher', 'school-admin', 'principal']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    # Ownership check — walk up: activity → topic → class
    activity = db.fetch_one(
        'SELECT topic_id FROM syllabus_activity WHERE activity_id = ?', (activity_id,)
    )
    if not activity:
        return jsonify({'success': False, 'message': 'Activity not found'})

    topic = db.fetch_one(
        'SELECT class_id FROM syllabus_topic WHERE topic_id = ?', (activity['topic_id'],)
    )
    if not topic:
        return jsonify({'success': False, 'message': 'Topic not found'})

    if session['role'] == 'teacher':
        cls = db.fetch_one(
            'SELECT class_id FROM class WHERE class_id = ? AND teacher_id = ?',
            (topic['class_id'], session['user_id'])
        )
    else:
        cls = db.fetch_one(
            'SELECT class_id FROM class WHERE class_id = ? AND organization_id = ?',
            (topic['class_id'], session['organization_id'])
        )
    if not cls:
        return jsonify({'success': False, 'message': 'Not authorized'})

    db.execute_query('DELETE FROM syllabus_activity WHERE activity_id = ?', (activity_id,))
    return jsonify({'success': True})


# ── Student: mark / unmark an activity complete ──────────────
@app.route('/syllabus/activity/<int:activity_id>/toggle-complete', methods=['POST'])
def toggle_activity_complete(activity_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] != 'student':
        return jsonify({'success': False, 'message': 'Students only'})

    existing = db.fetch_one(
        'SELECT completion_id FROM syllabus_activity_completion WHERE activity_id = ? AND student_id = ?',
        (activity_id, session['user_id'])
    )
    if existing:
        db.execute_query(
            'DELETE FROM syllabus_activity_completion WHERE activity_id = ? AND student_id = ?',
            (activity_id, session['user_id'])
        )
        completed = False
    else:
        db.execute_query(
            'INSERT INTO syllabus_activity_completion (activity_id, student_id) VALUES (?, ?)',
            (activity_id, session['user_id'])
        )
        completed = True

    return jsonify({'success': True, 'completed': completed})


# ── Student view of their class syllabus ────────────────────
@app.route('/my-syllabus/<int:class_id>')
def student_syllabus(class_id):
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    if session['role'] != 'student':
        return abort(403)

    # Confirm student is enrolled in this class
    enrolled = db.fetch_one(
        'SELECT * FROM class_enrollment WHERE class_id = ? AND student_id = ?',
        (class_id, session['user_id'])
    )
    if not enrolled:
        return abort(403)

    cls  = db.fetch_one('SELECT * FROM class WHERE class_id = ?', (class_id,))
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    topics = db.fetch_query(
        'SELECT * FROM syllabus_topic WHERE class_id = ? ORDER BY order_index ASC, created_at ASC',
        (class_id,)
    )

    topics_with_activities = []
    total_activities = 0
    total_completed  = 0

    for t in topics:
        activities = db.fetch_query('''
            SELECT sa.*,
                   p.title  AS program_title,
                   c.title  AS challenge_title,
                   CASE WHEN sac.completion_id IS NOT NULL THEN 1 ELSE 0 END AS is_completed
            FROM syllabus_activity sa
            LEFT JOIN program   p   ON sa.linked_program_id   = p.program_id
            LEFT JOIN challenge c   ON sa.linked_challenge_id = c.challenge_id
            LEFT JOIN syllabus_activity_completion sac
                   ON sac.activity_id = sa.activity_id AND sac.student_id = ?
            WHERE sa.topic_id = ?
            ORDER BY sa.order_index ASC, sa.created_at ASC
        ''', (session['user_id'], t['topic_id']))

        acts = [dict(a) for a in activities]
        topic_completed = sum(1 for a in acts if a['is_completed'])
        total_activities += len(acts)
        total_completed  += topic_completed

        topics_with_activities.append({
            **dict(t),
            'activities': acts,
            'topic_completed': topic_completed,
            'topic_total': len(acts)
        })

    overall_pct = round((total_completed / total_activities * 100) if total_activities else 0)

   
    return render_template('shared/student-syllabus.html',
        user=user,
        cls=dict(cls),
        topics=topics_with_activities,
        total_activities=total_activities,
        total_completed=total_completed,
        overall_pct=overall_pct,
    )

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
        sql = '''
            SELECT c.*,
                u.fullname as creator_name,
                (SELECT COUNT(*) FROM challenge_submission cs 
                    WHERE cs.challenge_id = c.challenge_id) as submission_count,
                (SELECT submission_id FROM challenge_submission cs
                    WHERE cs.challenge_id = c.challenge_id AND cs.student_id = ?) as my_submission_id,
                (SELECT ag.score FROM challenge_submission cs
                    JOIN assessment_grade ag ON ag.submission_id = cs.submission_id
                    WHERE cs.challenge_id = c.challenge_id AND cs.student_id = ?) as my_score,
                (SELECT ag.feedback FROM challenge_submission cs
                    JOIN assessment_grade ag ON ag.submission_id = cs.submission_id
                    WHERE cs.challenge_id = c.challenge_id AND cs.student_id = ?) as my_feedback,
                CASE WHEN c.deadline < ? THEN 'expired' ELSE 'active' END as status,
                -- NEW: check if this challenge is in the student's class syllabus
                CASE WHEN EXISTS (
                    SELECT 1 FROM syllabus_activity sa
                    JOIN syllabus_topic st ON sa.topic_id = st.topic_id
                    JOIN class_enrollment ce ON ce.class_id = st.class_id
                    WHERE sa.linked_challenge_id = c.challenge_id
                    AND ce.student_id = ?
                ) THEN 1 ELSE 0 END as is_in_syllabus
            FROM challenge c
            JOIN user u ON c.created_by = u.user_id
            JOIN challenge_class cc ON cc.challenge_id = c.challenge_id
            JOIN class_enrollment ce ON ce.class_id = cc.class_id AND ce.student_id = ?
            WHERE c.organization_id = ?
            GROUP BY c.challenge_id
            ORDER BY c.created_at DESC
        '''
        challenges = db.fetch_query(sql, (
            session['user_id'], session['user_id'], session['user_id'],
            now,
            session['user_id'],  # ← new param for is_in_syllabus
            session['user_id'], org_id,
        ))
        
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
    
    #attach linked_classes to each challenge for teacher view ──
    challenges_list = [dict(c) for c in challenges]
    if session['role'] in ['teacher', 'school-admin', 'principal']:
        for c in challenges_list:
            rows = db.fetch_query('''
                SELECT DISTINCT cl.name as class_name
                FROM syllabus_activity sa
                JOIN syllabus_topic st ON sa.topic_id = st.topic_id
                JOIN class cl ON st.class_id = cl.class_id
                WHERE sa.linked_challenge_id = ?
                AND cl.teacher_id = ?
            ''', (c['challenge_id'], session['user_id']))
            c['linked_classes'] = [r['class_name'] for r in rows]
    else:
        challenges_list = challenges_list  # already dicts, no linked_classes needed


    return render_template('shared/activity.html',
        user=user,
        challenges=challenges_list,
        active_count=active_count,
        completed_count=completed_count,
        points=points,
        leaderboard=leaderboard,
        species=species
    )


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

    # Auto-complete any syllabus activities linked to this challenge
    auto_complete_syllabus_activity(session['user_id'], 'challenge', challenge_id)

    
    return jsonify({
        'success': True,
        'points_earned': challenge['points'],
        'new_total': db.fetch_one('SELECT points FROM user WHERE user_id = ?', (session['user_id'],))['points']
    })

# Un-submit a challenge (student withdraws their submission)
@app.route('/unsubmit-challenge/<int:challenge_id>', methods=['POST'])
def unsubmit_challenge(challenge_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    if session['role'] not in ['student', 'community-member']:
        return jsonify({'success': False, 'message': 'Not authorized'})

    submission = db.fetch_one(
        'SELECT * FROM challenge_submission WHERE challenge_id = ? AND student_id = ?',
        (challenge_id, session['user_id'])
    )
    if not submission:
        return jsonify({'success': False, 'message': 'No submission found'})

    challenge = db.fetch_one(
        'SELECT * FROM challenge WHERE challenge_id = ?', (challenge_id,)
    )

    # Revoke points
    if challenge:
        db.execute_query(
            'UPDATE user SET points = MAX(0, points - ?) WHERE user_id = ?',
            (challenge['points'], session['user_id'])
        )

    # Delete media file from disk if exists
    if submission['media_path']:
        full_path = os.path.join('static', submission['media_path'])
        if os.path.exists(full_path):
            os.remove(full_path)

    # Delete the submission
    db.execute_query(
        'DELETE FROM challenge_submission WHERE challenge_id = ? AND student_id = ?',
        (challenge_id, session['user_id'])
    )

    # Remove syllabus activity completions linked to this challenge
    db.execute_query(
        '''DELETE FROM syllabus_activity_completion
           WHERE student_id = ?
           AND activity_id IN (
               SELECT activity_id FROM syllabus_activity
               WHERE activity_type = 'challenge' AND linked_challenge_id = ?
           )''',
        (session['user_id'], challenge_id)
    )

    new_points = db.fetch_one(
        'SELECT points FROM user WHERE user_id = ?', (session['user_id'],)
    )['points']

    return jsonify({'success': True, 'new_total': new_points})

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

#Get Creative Canvas page
# ── Render page ──────────────────────────────────────────────────────────────
@app.route('/creative-canvas')
def get_creative_canvas():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))

    user    = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    org_id  = session.get('organization_id')
    role    = session.get('role')

    # System-admin sees everything; others see their org only
    if role == 'system-admin':
        files = db.fetch_query('''
            SELECT cf.*, u.fullname as uploader_name, u.avatar as uploader_avatar,
                   u.role as uploader_role
            FROM creative_file cf
            JOIN user u ON cf.user_id = u.user_id
            ORDER BY cf.uploaded_at DESC
        ''')
    else:
        files = db.fetch_query('''
            SELECT cf.*, u.fullname as uploader_name, u.avatar as uploader_avatar,
                   u.role as uploader_role
            FROM creative_file cf
            JOIN user u ON cf.user_id = u.user_id
            WHERE u.organization_id = ?
            ORDER BY cf.uploaded_at DESC
        ''', (org_id,))

    species = db.fetch_query('SELECT common_name FROM species ORDER BY common_name')

    return render_template('shared/creative-canvas.html',
                           user=user,
                           files=[dict(f) for f in files],
                           species=species)


# ── Upload a file ─────────────────────────────────────────────────────────────
@app.route('/upload-creative-file', methods=['POST'])
def upload_creative_file():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    title       = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    species_tag = request.form.get('species_tag', '').strip()

    if not title:
        return jsonify({'success': False, 'message': 'Title is required'})

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    allowed_canvas = {'pdf', 'ppt', 'pptx', 'doc', 'docx', 'xls', 'xlsx', 'txt'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_canvas:
        return jsonify({'success': False, 'message': f'File type .{ext} is not supported'})

    # Map extension to display type category
    type_map = {
        'pdf': 'pdf',
        'ppt': 'ppt', 'pptx': 'ppt',
        'doc': 'doc', 'docx': 'doc',
        'xls': 'xls', 'xlsx': 'xls',
        'txt': 'doc'
    }
    file_type = type_map.get(ext, 'doc')

    # Save file
    filename        = secure_filename(file.filename)
    unique_filename = f"canvas_{session['user_id']}_{int(time.time())}_{filename}"
    os.makedirs(CREATIVE_CANVAS_FOLDER, exist_ok=True)
    save_path = os.path.join(CREATIVE_CANVAS_FOLDER, unique_filename)
    file.save(save_path)

    file_size = os.path.getsize(save_path)
    filepath  = f"uploads/creative-canvas/{unique_filename}"

    db.execute_query(
        '''INSERT INTO creative_file
           (user_id, title, description, species_tag, filename, filepath, file_type, file_size)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (session['user_id'], title, description,
         species_tag or None, filename, filepath, file_type, file_size)
    )

    new_file = db.fetch_one(
        'SELECT * FROM creative_file WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1',
        (session['user_id'],)
    )

    return jsonify({'success': True, 'file': dict(new_file)})


# ── Download a file ───────────────────────────────────────────────────────────
@app.route('/download-creative-file/<int:file_id>')
def download_creative_file(file_id):
    if 'user_id' not in session:
        return redirect(url_for('login_get'))

    record = db.fetch_one('SELECT * FROM creative_file WHERE file_id = ?', (file_id,))
    if not record:
        return abort(404)

    full_path = os.path.join('static', record['filepath'])
    if not os.path.exists(full_path):
        return abort(404)

    return send_file(full_path, as_attachment=True, download_name=record['filename'])


# ── Delete a file ─────────────────────────────────────────────────────────────
@app.route('/delete-creative-file/<int:file_id>', methods=['POST'])
def delete_creative_file(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    record = db.fetch_one('SELECT * FROM creative_file WHERE file_id = ?', (file_id,))
    if not record:
        return jsonify({'success': False, 'message': 'File not found'})

    # Owner, school-admin, principal, community-admin, system-admin can delete
    allowed_admin_roles = ['school-admin', 'principal', 'community-admin', 'system-admin']
    if record['user_id'] != session['user_id'] and session['role'] not in allowed_admin_roles:
        return jsonify({'success': False, 'message': 'Not authorized'})

    # Remove file from disk
    full_path = os.path.join('static', record['filepath'])
    if os.path.exists(full_path):
        os.remove(full_path)

    db.execute_query('DELETE FROM creative_file WHERE file_id = ?', (file_id,))
    return jsonify({'success': True})


# ── Get files (JSON, for dynamic refresh after upload) ────────────────────────
@app.route('/get-creative-files')
def get_creative_files():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    org_id = session.get('organization_id')
    role   = session.get('role')

    if role == 'system-admin':
        files = db.fetch_query('''
            SELECT cf.*, u.fullname as uploader_name, u.avatar as uploader_avatar,
                   u.role as uploader_role
            FROM creative_file cf
            JOIN user u ON cf.user_id = u.user_id
            ORDER BY cf.uploaded_at DESC
        ''')
    else:
        files = db.fetch_query('''
            SELECT cf.*, u.fullname as uploader_name, u.avatar as uploader_avatar,
                   u.role as uploader_role
            FROM creative_file cf
            JOIN user u ON cf.user_id = u.user_id
            WHERE u.organization_id = ?
            ORDER BY cf.uploaded_at DESC
        ''', (org_id,))

    return jsonify({'success': True, 'files': [dict(f) for f in files]})


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
        SELECT m.message_id, m.body, m.sent_at, m.sender_id, m.attachment,
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
        return jsonify({'users': []})
    
    q = request.args.get('q', '').strip()
    
    if q.startswith('id:'):
        user_id = q[3:]
        # No org filter — allows cross-org lookup for system-admin messaging
        users = db.fetch_query(
            'SELECT user_id, fullname, role, avatar FROM user WHERE user_id = ?',
            (user_id,)
        )
    else:
        users = db.fetch_query(
            '''SELECT user_id, fullname, role, avatar FROM user
               WHERE fullname LIKE ? AND organization_id = ? AND user_id != ?
               LIMIT 10''',
            (f'%{q}%', session['organization_id'], session['user_id'])
        )
    
    return jsonify({'users': [dict(u) for u in users]})

#Retriveving organization's data for its members or staff/students
@app.route('/my-organization')
def my_organization():
    if 'user_id' not in session:
        return redirect(url_for('login_get'))
    
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))
    
    if not user['organization_id']:
        return redirect(url_for('dashboard'))
    
    org = db.fetch_one('SELECT * FROM organization WHERE organization_id = ?', (user['organization_id'],))
    
    is_school = org['category'] == 'school'
    
    # Counts
    if is_school:
        member_count = db.fetch_one(
            "SELECT COUNT(*) as count FROM user WHERE organization_id = ? AND role = 'student'",
            (user['organization_id'],)
        )['count']
        staff_count = db.fetch_one(
            "SELECT COUNT(*) as count FROM user WHERE organization_id = ? AND role = 'teacher'",
            (user['organization_id'],)
        )['count']
        # Principal and admin
        leader = db.fetch_one(
            "SELECT * FROM user WHERE organization_id = ? AND role = 'principal' LIMIT 1",
            (user['organization_id'],)
        )
        admin = db.fetch_one(
            "SELECT * FROM user WHERE organization_id = ? AND role = 'school-admin' LIMIT 1",
            (user['organization_id'],)
        )
        # Staff list
        staff = db.fetch_query(
            "SELECT * FROM user WHERE organization_id = ? AND role = 'teacher'",
            (user['organization_id'],)
        )
    else:
        member_count = db.fetch_one(
            "SELECT COUNT(*) as count FROM user WHERE organization_id = ? AND role = 'community-member'",
            (user['organization_id'],)
        )['count']
        staff_count = None
        leader = None
        admin = db.fetch_one(
            "SELECT * FROM user WHERE organization_id = ? AND role = 'community-admin' LIMIT 1",
            (user['organization_id'],)
        )
        staff = db.fetch_query(
            "SELECT * FROM user WHERE organization_id = ? AND role = 'community-member'",
            (user['organization_id'],)
        )

    return render_template('shared/my-organization.html',
        user=user,
        org=org,
        is_school=is_school,
        member_count=member_count,
        staff_count=staff_count,
        leader=leader,
        admin=admin,
        staff=staff
    )

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
    user = db.fetch_one('SELECT * FROM user WHERE user_id = ?', (session['user_id'],))

    if user['role'] == 'system-admin':
        # All sightings but show org name instead of student details
        sql = '''SELECT s.*, sp.common_name, sp.species_id as sp_id,
            o.name as reporter_name, o.category as reporter_role, o.avatar as reporter_avatar
            FROM sighting s
            JOIN species sp ON s.species_id = sp.species_id
            JOIN user u ON s.user_id = u.user_id
            LEFT JOIN organization o ON u.organization_id = o.organization_id
            ORDER BY s.submitted_at DESC'''
        sightings = db.fetch_query(sql)

    elif user['role'] in ['school-admin', 'principal']:
        # All sightings from their school
        sql = '''SELECT s.*, sp.common_name, sp.species_id as sp_id,
            u.fullname as reporter_name, u.role as reporter_role, u.avatar as reporter_avatar
            FROM sighting s
            JOIN species sp ON s.species_id = sp.species_id
            JOIN user u ON s.user_id = u.user_id
            WHERE u.organization_id = ?
            ORDER BY s.submitted_at DESC'''
        sightings = db.fetch_query(sql, (user['organization_id'],))

    elif user['role'] == 'teacher':
        # Only sightings from students in their classes
        sql = '''SELECT s.*, sp.common_name, sp.species_id as sp_id,
            u.fullname as reporter_name, u.role as reporter_role, u.avatar as reporter_avatar
            FROM sighting s
            JOIN species sp ON s.species_id = sp.species_id
            JOIN user u ON s.user_id = u.user_id
            WHERE u.user_id IN (
                SELECT DISTINCT ce.student_id
                FROM class_enrollment ce
                JOIN class c ON ce.class_id = c.class_id
                WHERE c.teacher_id = ?
            )
            ORDER BY s.submitted_at DESC'''
        sightings = db.fetch_query(sql, (session['user_id'],))

    elif user['role'] == 'community-admin':
        # All sightings from their community
        sql = '''SELECT s.*, sp.common_name, sp.species_id as sp_id,
            u.fullname as reporter_name, u.role as reporter_role, u.avatar as reporter_avatar
            FROM sighting s
            JOIN species sp ON s.species_id = sp.species_id
            JOIN user u ON s.user_id = u.user_id
            WHERE u.organization_id = ?
            ORDER BY s.submitted_at DESC'''
        sightings = db.fetch_query(sql, (user['organization_id'],))

    else:
        # Students, community members, public — only their own
        sql = '''SELECT s.*, sp.common_name, sp.species_id as sp_id,
            u.fullname as reporter_name, u.role as reporter_role, u.avatar as reporter_avatar
            FROM sighting s
            JOIN species sp ON s.species_id = sp.species_id
            JOIN user u ON s.user_id = u.user_id
            WHERE s.user_id = ?
            ORDER BY s.submitted_at DESC'''
        sightings = db.fetch_query(sql, (session['user_id'],))

    return render_template('shared/sighting-reports-view.html', user=user, sightings=sightings)

#Deleting sighting reports logic
@app.route('/delete-sighting/<int:sighting_id>', methods=['POST'])
def delete_sighting(sighting_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    allowed_roles = ['teacher', 'school-admin', 'principal', 'community-admin']

    sighting = db.fetch_one(
        'SELECT user_id, species_id FROM sighting WHERE sighting_id = ?', (sighting_id,)
    )
    if not sighting:
        return jsonify({'success': False, 'message': 'Sighting not found'})

    if session['role'] not in allowed_roles:
        if sighting['user_id'] != session['user_id']:
            return jsonify({'success': False, 'message': 'Not authorized'})

    owner_id   = sighting['user_id']
    species_id = sighting['species_id']

    db.execute_query('DELETE FROM sighting WHERE sighting_id = ?', (sighting_id,))

    # Check if the owner has any remaining sightings of this specific species
    remaining = db.fetch_one(
        'SELECT COUNT(*) as count FROM sighting WHERE user_id = ? AND species_id = ?',
        (owner_id, species_id)
    )['count']

    # If no sightings of this species remain, unmark syllabus activities
    # that are sighting-type and linked to this specific species
    if remaining == 0:
        db.execute_query(
            '''DELETE FROM syllabus_activity_completion
               WHERE student_id = ?
               AND activity_id IN (
                   SELECT activity_id FROM syllabus_activity
                   WHERE activity_type = 'sighting'
                   AND linked_species_id = ?
               )''',
            (owner_id, species_id)
        )

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
    
    # Auto-complete any linked sighting activities in the syllabus
    auto_complete_syllabus_activity(session['user_id'], 'sighting', request.form.get('species_id'))
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(
        debug=True,
        host = '0.0.0.0',
        port = 5000
    )