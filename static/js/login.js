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

// Event listner to handle Registration input fields
let accessCodeRequest = false;
let accessCode = null;
let orgInfoStep = false;
let orgVerified = false;
document.getElementById('register-role').addEventListener('change', function(){
    const role = this.value;
    const needsAccessCode = ['student',];
    const needsOrgInfo = ['school-admin', 'community-admin'];
    const needsOrgVerify = ['teacher', 'principal', 'community-member']
    const btn = document.getElementById('register-btn');

    accessCodeRequest = false;
    accessCode = null;
    orgInfoStep = false;
    orgVerified = false;

    document.getElementById('org-group').style.display = 'none';
    document.getElementById('school-fields').style.display = 'none';
    document.getElementById('community-fields').style.display = 'none';
    document.getElementById('password-group').style.display = 'none';
    document.getElementById('confirm-password-group').style.display = 'none';
    document.getElementById('register-code-group').style.display = 'none';
    document.getElementById('org-select-group').style.display = 'none';

    if (needsAccessCode.includes(role)) {
        //Hide password fields until access code is retrieved
        accessCodeRequest = false;
        accessCode = null;
        btn.textContent = 'Request Access Code';
    }else if (needsOrgVerify.includes(role)){
        //Show org dropdown - shools for teacher / principal, and communities for community-members
        const category = (role === "community-member") ? 'community' : 'school';
        loadOrganizations(category);
        document.getElementById('org-select-group').style.display = 'block';
        btn.textContent = 'Next'  
    }else if (needsOrgInfo.includes(role)) {
        //Show password fields for step 1
        document.getElementById('password-group').style.display = 'block';
        document.getElementById('confirm-password-group').style.display = 'block';
        btn.textContent = 'Next';
    }else {
        //All other roles - one step
        document.getElementById('password-group').style.display = 'block';
        document.getElementById('confirm-password-group').style.display = 'block';
        document.getElementById('register-code-group').style.display = 'none';
        btn.textContent = 'Create Account';
    }
});


// ===================================================
// HANDLE LOGIN
// Only needs: role + email + password (no access code)
// ===================================================
function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    // Validation
    if (!email || !password) {
        alert('Please fill in all fields');
        return;
    }

    fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password})
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Save basic info to localStorage for dashboard JS 
            localStorage.setItem('user', JSON.stringify({
                name: data.fullname,
                role: data.role,
                email: email
            }));
            // Redirect to correct dashboard
            window.location.href = data.redirectTo;
        }else {
            alert(data.message || 'Invalid email or password');
        }
    })
    .catch (() => alert("Server error. Please try again"));
}

//Fetches org names from DB and populates the dropdown
function loadOrganizations(category){
    fetch(`/get-organizations?category=${category}`)
    .then(res => res.json())
    .then(data =>{
        const select = document.getElementById('org-select');
        select.innerHTML = '<option value="">Select your organization</option>';
        data.organizations.forEach(org => {
            const opt = document.createElement('option');
            opt.value = org.organization_id;
            opt.textContent = org.name;
            select.appendChild(opt);
        });
    })
    .catch(() => alert('Could not load organizations. Please try again'));
}

// HANDLE REGISTER
// student + teacher → need access code
// School admin + Community admin need to provide organisations details
// all others → only email + password
async function handleRegister(event) {
    event.preventDefault();

    const role = document.getElementById('register-role').value;
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const needsAccessCode = ['student',];
    const needsOrgVerify = ['teacher', 'principal', 'community-member'];
    const needsOrgInfo = ['school-admin', 'community-admin'];

    if (!role || !name || !email) {
        alert("Please fill in all fields");
        return;
    }

    // ===== Student / Teacher registration Flow which needs access code =====
    if (needsAccessCode.includes(role)) {
        // STEP 1 -- request access code
        if (!accessCodeRequest) {
            fetch('/access-code-request', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({role, name, email})
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    accessCode = data.accessCode;
                    document.getElementById('register-code').value = data.accessCode;
                    alert(`Access code found! ${accessCode} Please enter it below.`);
                    
                    document.getElementById('register-code-group').style.display = 'block';
                    document.getElementById('password-group').style.display = 'block';
                    document.getElementById('confirm-password-group').style.display = 'block';
                    document.getElementById('register-btn').textContent = 'Create Account';
                    accessCodeRequest = true;   
                }else {
                    alert('Error: ' + (data.message || 'No registration found for this email.'));
                }
            })
            .catch(() => alert('Server error. Please try again'));
            return;
        }
        // STEP 2 - verify access code + register
        const accessCode2 = document.getElementById('register-code').value;
        const password = document.getElementById('register-password').value;
        const confirmPassword = document.getElementById('register-confirm').value;
        
        if (!accessCode2) {alert('Please enter your access code');return;}
        if (accessCode2 !== accessCode) {alert('Incorrect access code. Please check and try again.');return;}
        if (!password || !confirmPassword) {alert('Please enter and confirm your password');return;}
        if (password !== confirmPassword) {alert('Passwords do not match');return;}
        
        sendRegistration(role, name, email, password, accessCode2, null);

    // Teacher / Principal / Community Member
    }else if (needsOrgVerify.includes(role)) {
        // Step 1 - check they exist in registration table
        if (!orgVerified){
            const orgId = document.getElementById('org-select').value;
            if (!orgId) {alert('Please select your organization'); return; }

            fetch('/verify-registration', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, role, organization_id: orgId})
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    orgVerified = true;
                    document.getElementById('password-group').style.display = 'block';
                    document.getElementById('confirm-password-group').style.display = 'block';
                    document.getElementById('register-btn').textContent = 'Create Account';
                }else {
                    alert('Error: ' + (data.message || 'Registration not found.'));
                }
            })
            .catch(() => alert('Server error. Please try again. '));
            return;
        }

        //Step 2 - create account
        const orgId = document.getElementById('org-select').value;
        const password = document.getElementById('register-password').value;
        const confirmPassword = document.getElementById('register-confirm').value;
        if (!password || !confirmPassword) { alert('Please enter and confirm your password'); return; }
        if (password !== confirmPassword) { alert('Passwords do not match'); return; }

        sendRegistration(role, name, email, password, null, null, orgId);


    // ===== School Admin / Community Admin =====  
    }else if (needsOrgInfo.includes(role)) {
        // Step 1 - personal info + password
        if (!orgInfoStep) {
            const password = document.getElementById('register-password').value;
            const confirmPassword = document.getElementById('register-confirm').value;
            
            if (!password || !confirmPassword) {alert('Please enter and confirm your password'); return;}
            if (password !== confirmPassword) {alert('Password do not match'); return; }

            // Show org fields
            document.getElementById('org-group').style.display='block';
            if (role === 'school-admin') {
                document.getElementById('school-fields').style.display = 'block';
                document.getElementById('community-fields').style.display = 'none';
            }else {
                document.getElementById('community-fields').style.display = 'block';
                document.getElementById('school-fields').style.display = 'none';
            }
            document.getElementById('register-btn').textContent = 'Create Account';
            orgInfoStep = true;
            return;
        }

        // Step 2 - org info + submit
        const password = document.getElementById('register-password').value;
        let orgData = {};

        if (role === 'school-admin') {
            const schoolName = document.getElementById('school-name').value;
            const schoolAddress = document.getElementById('school-address').value;
            const schoolType = document.getElementById('school-type').value;
            if (!schoolName || !schoolAddress || !schoolType) {
                alert('Please fill in all school information');
                return;
            }
            orgData = { name: schoolName, address: schoolAddress, type: schoolType, email: email };
        }else {
            const communityName = document.getElementById('community-name').value;
            const communityAddress = document.getElementById('community-address').value;
            const communityType = document.getElementById('community-type').value;
            if (!communityName || !communityAddress || !communityType) {
                alert('Please fill in all community information');
                return;
            }
            orgData = { name: communityName, address: communityAddress, type: communityType, email: email };
        }

        sendRegistration(role, name, email, password, null, orgData);

    //===== All Other Roles -- One Step =====    
    } else {
        const password = document.getElementById('register-password').value;
        const confirmPassword = document.getElementById('register-confirm').value;
        if (!password || !confirmPassword) {alert('Please enter and confirm your password'); return; }
        if (password !== confirmPassword) {alert('Passwords do not match'); return;}
        
        sendRegistration(role, name, email, password, null, null);
    }
}

    // Send Registration Details to Flask Server
function sendRegistration(role, name, email, password, accessCodeParam, orgData, orgId = null) {
    fetch('/register-account', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ role, name, email, password, accessCodeParam, orgData, orgId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert('Account created!\n\nName: ' + name + '\nRole: ' + role + '\nEmail: ' + email + '\n\n[Please sign in]');
            // Reset everything
            accessCode = null;
            accessCodeRequest = false;
            orgInfoStep = false;
            orgVerified = false;
            document.getElementById('register-btn').textContent = 'Create Account';
            document.getElementById('register-code-group').style.display = 'none';
            document.getElementById('password-group').style.display = 'none';
            document.getElementById('confirm-password-group').style.display = 'none';
            document.getElementById('org-group').style.display = 'none';
            document.getElementById('school-fields').style.display = 'none';
            document.getElementById('community-fields').style.display = 'none';
            switchTab('login');
        } else {
            alert('Registration failed: ' + (data.message || 'Unknown error'));
        }
    }).catch(() => {
        alert ('Server error. Please try again.');
        orgInfoStep = false;
        accessCodeRequest = false;
        accessCode = null;
        orgVerified = false;
        document.getElementById('register-btn').textContent = 'Next';
        document.getElementById('org-group').style.display = 'none';
        document.getElementById('school-fields').style.display = 'none';
        document.getElementById('community-fields').style.display = 'none';      
    });
}

