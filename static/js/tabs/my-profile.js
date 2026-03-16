// ===== MY PROFILE JS =====

// Check user authentication
const user = JSON.parse(localStorage.getItem('user'));

if (!user) {
    window.location.href = '../login.html';
}

// Update UI with user info
if (user) {
    const navUsername = document.getElementById('nav-username');
    if (navUsername) navUsername.textContent = user.name;

    const roleBadge = document.getElementById('user-role-badge');
    if (roleBadge) {
        const roleNames = {
            'student': 'Student',
            'teacher': 'Teacher',
            'principal': 'Principal',
            'school-admin': 'School Admin',
            'community-member': 'Community',
            'community-admin': 'Community Admin',
            'system-admin': 'System Admin',
            'public': 'Guest'
        };
        roleBadge.textContent = roleNames[user.role] || user.role;
    }

    // Load profile data
    loadProfileData();
}

// Sign out function
function signOut() {
    localStorage.removeItem('user');
    window.location.href = '/logout';
}

// Toggle sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

// ===== LOAD PROFILE DATA =====
function loadProfileData() {
    // Load avatar (use saved avatar or default 👤)
    const avatarDisplay = document.querySelector('.profile-avatar-large');
    if (avatarDisplay) {
        avatarDisplay.textContent = user.avatar || '👤';
    }
    
    // Load basic info
    document.getElementById('profile-name').textContent = user.name || 'User';
    document.getElementById('profile-role').textContent = getRoleName(user.role);
    document.getElementById('profile-email').textContent = user.email || 'email@example.com';
    
    // Load personal info
    document.getElementById('display-name').textContent = user.name || 'Not provided';
    document.getElementById('display-email').textContent = user.email || 'Not provided';
    document.getElementById('display-phone').textContent = user.phone || 'Not provided';
    document.getElementById('display-location').textContent = user.location || 'Not provided';
    
    // Set input values for editing
    document.getElementById('edit-name').value = user.name || '';
    document.getElementById('edit-email').value = user.email || '';
    document.getElementById('edit-phone').value = user.phone || '';
    document.getElementById('edit-location').value = user.location || '';
    
    // Load organization info based on role
    loadOrganizationInfo();
}

function getRoleName(role) {
    const roleNames = {
        'student': 'Student',
        'teacher': 'Teacher',
        'principal': 'Principal',
        'school-admin': 'School Administrator',
        'community-member': 'Community Member',
        'community-admin': 'Community Administrator',
        'system-admin': 'System Administrator',
        'public': 'Public User'
    };
    return roleNames[role] || role;
}

function loadOrganizationInfo() {
    const orgSection = document.getElementById('org-section-title');
    const orgLabel = document.getElementById('org-label');
    const orgDisplay = document.getElementById('display-org');
    const gradeItem = document.getElementById('grade-item');
    
    if (user.role === 'student' || user.role === 'teacher' || user.role === 'principal' || user.role === 'school-admin') {
        orgSection.textContent = 'School Information';
        orgLabel.textContent = 'School Name';
        orgDisplay.textContent = user.school || 'Jakarta International School';
        
        if (user.role === 'student') {
            gradeItem.style.display = 'block';
            document.getElementById('display-grade').textContent = user.grade || 'Grade 10';
        } else {
            gradeItem.style.display = 'none';
        }
    } else if (user.role === 'community-member' || user.role === 'community-admin') {
        orgSection.textContent = 'Community Information';
        orgLabel.textContent = 'Community Name';
        orgDisplay.textContent = user.community || 'Jakarta Conservation Community';
        gradeItem.style.display = 'none';
    } else {
        document.getElementById('organization-section').style.display = 'none';
    }
}

// ===== EDIT FUNCTIONALITY =====
function toggleEdit(section) {
    const infoSection = document.getElementById(`${section}-info`);
    const actionsSection = document.getElementById(`${section}-actions`);
    const editBtn = document.querySelector('.btn-edit');
    
    // Get current state
    const isEditing = actionsSection.style.display === 'flex';
    
    // Toggle display/edit mode
    const displays = infoSection.querySelectorAll('p');
    const inputs = infoSection.querySelectorAll('input');
    
    if (isEditing) {
        // Switch back to display mode
        displays.forEach(p => p.style.display = 'block');
        inputs.forEach(input => input.style.display = 'none');
        actionsSection.style.display = 'none';
        editBtn.style.display = 'inline-block';
    } else {
        // Switch to edit mode
        displays.forEach(p => p.style.display = 'none');
        inputs.forEach(input => input.style.display = 'block');
        actionsSection.style.display = 'flex';
        editBtn.style.display = 'none';
    }
}

function cancelEdit(section) {
    // Reset input values to original
    document.getElementById('edit-name').value = user.name || '';
    document.getElementById('edit-email').value = user.email || '';
    document.getElementById('edit-phone').value = user.phone || '';
    document.getElementById('edit-location').value = user.location || '';
    
    // Toggle back to display mode
    toggleEdit(section);
}

function saveEdit(section) {
    // Get updated values
    const newName = document.getElementById('edit-name').value;
    const newEmail = document.getElementById('edit-email').value;
    const newPhone = document.getElementById('edit-phone').value;
    const newLocation = document.getElementById('edit-location').value;
    
    // Update user object
    user.name = newName;
    user.email = newEmail;
    user.phone = newPhone;
    user.location = newLocation;
    
    // Save to localStorage
    localStorage.setItem('user', JSON.stringify(user));
    
    // Update displays
    document.getElementById('profile-name').textContent = newName;
    document.getElementById('profile-email').textContent = newEmail;
    document.getElementById('display-name').textContent = newName || 'Not provided';
    document.getElementById('display-email').textContent = newEmail || 'Not provided';
    document.getElementById('display-phone').textContent = newPhone || 'Not provided';
    document.getElementById('display-location').textContent = newLocation || 'Not provided';
    
    // Update nav
    document.getElementById('nav-username').textContent = newName;
    
    // Toggle back to display mode
    toggleEdit(section);
    
    alert('Profile updated successfully!');
}

// ===== SETTINGS =====
function toggleSetting(type) {
    const checkbox = document.getElementById(`${type}-notifications`) || document.getElementById('public-profile');
    const status = checkbox.checked ? 'enabled' : 'disabled';
    console.log(`${type} notifications ${status}`);
    // TODO: Save to backend
}

// ===== CHANGE PASSWORD =====
function changePassword() {
    const current = document.getElementById('current-password').value;
    const newPass = document.getElementById('new-password').value;
    const confirm = document.getElementById('confirm-password').value;
    
    if (!current || !newPass || !confirm) {
        alert('Please fill in all password fields');
        return;
    }
    
    if (newPass !== confirm) {
        alert('New passwords do not match');
        return;
    }
    
    if (newPass.length < 6) {
        alert('Password must be at least 6 characters long');
        return;
    }
    
    // TODO: Verify current password and update
    alert('Password updated successfully!');
    
    // Clear fields
    document.getElementById('current-password').value = '';
    document.getElementById('new-password').value = '';
    document.getElementById('confirm-password').value = '';
}

// ===== CHANGE AVATAR =====
function changeAvatar() {
    document.getElementById('avatar-modal').style.display = 'flex';
}

function closeAvatarModal() {
    document.getElementById('avatar-modal').style.display = 'none';
}

function selectAvatar(emoji) {
    // Update avatar everywhere
    document.querySelector('.profile-avatar-large').textContent = emoji;
    
    // Save to user object
    user.avatar = emoji;
    localStorage.setItem('user', JSON.stringify(user));
    
    // Close modal
    closeAvatarModal();
    
    console.log('Avatar changed to:', emoji);
}

// ===== DELETE ACCOUNT =====
function deleteAccount() {
    const confirmed = confirm('Are you absolutely sure you want to delete your account?\n\nThis action cannot be undone. All your data will be permanently deleted.');
    
    if (confirmed) {
        const doubleCheck = confirm('Final confirmation: Delete your account and all data?');
        
        if (doubleCheck) {
            // TODO: Send delete request to backend
            localStorage.removeItem('user');
            alert('Account deleted. You will be redirected to the login page.');
            window.location.href = '../login.html';
        }
    }
}

console.log('My Profile loaded successfully');