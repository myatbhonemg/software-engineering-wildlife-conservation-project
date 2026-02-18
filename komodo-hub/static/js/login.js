// TAB SWITCHER
// Switches between Sign In and Register tabs
function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Update form content
    document.querySelectorAll('.form-content').forEach(form => {
        form.classList.remove('active');
    });

    // Activate selected tab
    if (tab === 'login') {
        document.querySelectorAll('.tab-btn')[0].classList.add('active');
        document.getElementById('login-form').classList.add('active');
    } else {
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
        document.getElementById('register-form').classList.add('active');
    }
}


// PASSWORD TOGGLE
function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    if (field.type === 'password') {
        field.type = 'text';
    } else {
        field.type = 'password';
    }
}



// ROLE PRIVILEGES

const rolePrivileges = {
    'student': {
        name: 'Student',
        canAccess: ['View conservation programs', 'Submit sighting reports', 'Access school library', 'Create creative canvas', 'Message assigned teacher'],
        cannotAccess: ['View other student profiles', 'Manage classes', 'Access admin dashboard'],
        redirectTo: 'student-dashboard.html'
    },
    'teacher': {
        name: 'Teacher',
        canAccess: ['Manage class syllabus', 'View enrolled student data', 'Leave notes on student work', 'Message students', 'Create class activities'],
        cannotAccess: ['View students outside assigned class', 'Manage school subscriptions', 'Access system admin panel'],
        redirectTo: 'teacher-dashboard.html'
    },
    'school-admin': {
        name: 'School Administrator',
        canAccess: ['Manage school subscriptions', 'Register and enroll students', 'Generate student access codes', 'View teacher and student data'],
        cannotAccess: ['Access other school data', 'Manage system-wide settings'],
        redirectTo: 'school-admin-dashboard.html'
    },
    'system-admin': {
        name: 'System Administrator',
        canAccess: ['Manage all school accounts', 'Manage all community accounts', 'View business dashboard', 'Full system access'],
        cannotAccess: ['Modify source code'],
        redirectTo: 'system-admin-dashboard.html'
    },
    'community-member': {
        name: 'Community Member',
        canAccess: ['Upload articles and essays', 'Submit sighting reports', 'View public library', 'Manage own profile page'],
        cannotAccess: ['Manage community account', 'Register other members'],
        redirectTo: 'community-dashboard.html'
    },
    'community-admin': {
        name: 'Community Administrator',
        canAccess: ['Manage community account', 'Register community members', 'View member contributions', 'Manage community library'],
        cannotAccess: ['Access school data', 'Manage system-wide settings'],
        redirectTo: 'community-admin-dashboard.html'
    },
    'principal': {
        name: 'School Principal',
        canAccess: ['Approve and decline student registrations', 'View all teachers and students', 'View school reports', 'Manage school conservation programs'],
        cannotAccess: ['Access other school data', 'Manage system-wide settings'],
        redirectTo: 'principal-dashboard.html'
    },
    'public': {
        name: 'General Public',
        canAccess: ['Browse species knowledge base', 'View school and community library pages', 'Explore conservation programs'],
        cannotAccess: ['Submit sighting reports', 'Join programs', 'Access any dashboard'],
        redirectTo: 'public-dashboard.html'
    }
};


// ===================================================
// HANDLE LOGIN
// Only needs: role + email + password (no access code)
// ===================================================
function handleLogin(event) {
    event.preventDefault();

    const role = document.getElementById('login-role').value;
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    // Validation
    if (!role) {
        alert('Please select your role');
        return;
    }
    if (!email || !password) {
        alert('Please fill in all fields');
        return;
    }

    // Get privileges for this role
    const privileges = rolePrivileges[role];
    const canAccessList = privileges.canAccess.map(p => '   ✅ ' + p).join('\n');
    const cannotAccessList = privileges.cannotAccess.map(p => '   ❌ ' + p).join('\n');
    // Save user to localStorage so dashboard can read it
    localStorage.setItem('user', JSON.stringify({
        name: email.split('@')[0],
        role: role,
        email: email
    }));

    // Redirect to correct dashboard
    window.location.href = privileges.redirectTo;
    
}


// HANDLE REGISTER
// student + teacher + community-member → need access code
// all others → only email + password
let accessCodeRequest = false;
function handleRegister(event) {
    event.preventDefault();

    const role = document.getElementById('register-role').value;
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const needsAccessCode = ['student', 'teacher', 'community-member'];

    // Validation
    if (!accessCodeRequest){
        if (!role || !name || !email) {
            alert('Please fill in all fields');
            return;
        }
        if (needsAccessCode.includes(role)) {
            //fake backend email
            alert('Request sent!\n\nIf your email is approved, you will receive an access code shortly.');

            // Show access code + password fields
            document.getElementById('register-code-group').style.display = 'block';
            document.getElementById('password-group').style.display = 'block';
            document.getElementById('confirm-password-group').style.display = 'block';
        }else{
            // school-admin, community-admin, system-admin, public
            // no access code needed, just show password fields
            document.getElementById('password-group').style.display = 'block';
            document.getElementById('confirm-password-group').style.display = 'block';
        }
        // Change button text to Step 2
        document.getElementById('register-btn').textContent = 'Create Account';
        accessCodeRequest = true;
        return;
    }
    // ===== STEP 2 =====
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm').value;

    if (needsAccessCode.includes(role)) {
        const accessCode = document.getElementById('register-code').value;
        if (!accessCode) {
            alert('Please enter your access code');
            return;
        }
    }
    if (!password || !confirmPassword) {
        alert('Please enter and confirm your password');
        return;
    }
    if (password !== confirmPassword) {
        alert('Passwords do not match');
        return;
    }

    // Success - show message and switch back to login
    alert('✅ Account created!\n\nName: ' + name + '\nRole: ' + rolePrivileges[role].name + '\nEmail: ' + email + '\n\n[Please sign in with your new account]');
    document.getElementById('register-btn').textContent = 'Request Access Code';
    document.getElementById('register-code-group').style.display = 'none';
    document.getElementById('password-group').style.display = 'none';
    document.getElementById('confirm-password-group').style.display = 'none';

    switchTab('login');
}