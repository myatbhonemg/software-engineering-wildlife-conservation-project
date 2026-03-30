// ===== MY PROFILE JS =====

function signOut() {
    localStorage.removeItem('user');
    window.location.href = '/logout';
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

// ===================================================================
// PERSONAL INFO EDIT (all roles)
// ===================================================================
function toggleEdit(section) {
    const infoSection = document.getElementById(`${section}-info`);
    const actionsSection = document.getElementById(`${section}-actions`);
    const editBtn = document.querySelector(`#${section}-info`)
                            ?.closest('.profile-section')
                            ?.querySelector('.btn-edit');

    const isEditing = actionsSection.style.display === 'flex';

    const displays = infoSection.querySelectorAll('p');
    const inputs   = infoSection.querySelectorAll('input');

    if (isEditing) {
        displays.forEach(p => p.style.display = 'block');
        inputs.forEach(i => i.style.display = 'none');
        actionsSection.style.display = 'none';
        if (editBtn) editBtn.style.display = 'inline-block';
    } else {
        displays.forEach(p => p.style.display = 'none');
        inputs.forEach(i => i.style.display = 'block');
        actionsSection.style.display = 'flex';
        if (editBtn) editBtn.style.display = 'none';
    }
}

function cancelEdit(section) {
    // Restore original values from display elements
    const name     = document.getElementById('display-name');
    const email    = document.getElementById('display-email');
    const phone    = document.getElementById('display-phone');
    const location = document.getElementById('display-location');

    if (name)     document.getElementById('edit-name').value     = name.textContent;
    if (email)    document.getElementById('edit-email').value    = email.textContent;
    if (phone)    document.getElementById('edit-phone').value    = phone.textContent === 'Not provided' ? '' : phone.textContent;
    if (location) document.getElementById('edit-location').value = location.textContent === 'Not provided' ? '' : location.textContent;

    toggleEdit(section);
}

function saveEdit(section) {
    const newName     = document.getElementById('edit-name').value.trim();
    const newEmail    = document.getElementById('edit-email').value.trim();
    const newPhone    = document.getElementById('edit-phone').value.trim();
    const newLocation = document.getElementById('edit-location').value.trim();

    if (!newName || !newEmail) {
        alert('Name and email are required.');
        return;
    }

    fetch('/update-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fullname: newName, email: newEmail, phone: newPhone, location: newLocation })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            // Update all display elements
            const profileName = document.getElementById('profile-name');
            if (profileName) profileName.textContent = newName;

            const profileEmail = document.querySelector('.profile-email-text');
            if (profileEmail) profileEmail.textContent = newEmail;

            document.getElementById('display-name').textContent     = newName     || 'Not provided';
            document.getElementById('display-email').textContent    = newEmail    || 'Not provided';
            document.getElementById('display-phone').textContent    = newPhone    || 'Not provided';
            document.getElementById('display-location').textContent = newLocation || 'Not provided';

            toggleEdit(section);
            alert('Personal information updated successfully!');
        } else {
            alert('Error: ' + (data.message || 'Update failed'));
        }
    })
    .catch(() => alert('Server error. Please try again.'));
}

// ===================================================================
// ORGANISATION EDIT (school-admin / community-admin only)
// ===================================================================
function toggleOrgEdit() {
    const infoSection    = document.getElementById('org-info');
    const actionsSection = document.getElementById('org-edit-actions');
    const editBtn        = document.getElementById('org-edit-btn');

    const isEditing = actionsSection.style.display === 'flex';

    // Toggle display <-> input for each field
    const pairs = [
        ['org-disp-name',    'org-edit-name'],
        ['org-disp-type',    'org-edit-type'],
        ['org-disp-email',   'org-edit-email'],
        ['org-disp-address', 'org-edit-address'],
    ];

    pairs.forEach(([dispId, inputId]) => {
        const disp  = document.getElementById(dispId);
        const input = document.getElementById(inputId);
        if (!disp || !input) return;
        if (isEditing) {
            disp.style.display  = 'block';
            input.style.display = 'none';
        } else {
            disp.style.display  = 'none';
            input.style.display = 'block';
        }
    });

    actionsSection.style.display = isEditing ? 'none' : 'flex';
    editBtn.style.display        = isEditing ? 'inline-block' : 'none';
}

function cancelOrgEdit() {
    // Restore inputs back to current display values
    const pairs = [
        ['org-disp-name',    'org-edit-name'],
        ['org-disp-email',   'org-edit-email'],
        ['org-disp-address', 'org-edit-address'],
    ];
    pairs.forEach(([dispId, inputId]) => {
        const disp  = document.getElementById(dispId);
        const input = document.getElementById(inputId);
        if (disp && input) input.value = disp.textContent === '—' ? '' : disp.textContent;
    });
    toggleOrgEdit();
}

function saveOrgEdit() {
    const name    = document.getElementById('org-edit-name')?.value.trim();
    const type    = document.getElementById('org-edit-type')?.value;
    const email   = document.getElementById('org-edit-email')?.value.trim();
    const address = document.getElementById('org-edit-address')?.value.trim();

    if (!name || !email) {
        alert('Organisation name and email are required.');
        return;
    }

    fetch('/update-org-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, type, email, address })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            // Update display text
            document.getElementById('org-disp-name').textContent    = name    || '—';
            document.getElementById('org-disp-type').textContent    = type ? type.replace(/-/g,' ').replace(/\b\w/g,c=>c.toUpperCase()) : '—';
            document.getElementById('org-disp-email').textContent   = email   || '—';
            document.getElementById('org-disp-address').textContent = address || '—';

            // Update card header
            const orgDisplayName = document.getElementById('org-display-name');
            if (orgDisplayName) orgDisplayName.textContent = name;

            const orgEmailEl = document.querySelector('.profile-header .profile-email-text');
            // Only update the first card's email (org card)
            const allEmailEls = document.querySelectorAll('.profile-email-text');
            if (allEmailEls[0]) allEmailEls[0].textContent = email;

            toggleOrgEdit();
            alert('Organisation profile updated successfully!');
        } else {
            alert('Error: ' + (data.message || 'Update failed'));
        }
    })
    .catch(() => alert('Server error. Please try again.'));
}

// ===================================================================
// USER AVATAR UPLOAD
// ===================================================================
function uploadAvatar(input) {
    const file = input.files[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
        alert('File too large. Max 5MB.');
        return;
    }

    const formData = new FormData();
    formData.append('avatar', file);

    fetch('/update-avatar', {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const avatarEl = document.getElementById('profile-avatar-img');
            const img = document.createElement('img');
            img.src       = data.avatar_url;
            img.className = 'profile-avatar-large';
            img.id        = 'profile-avatar-img';
            img.alt       = 'Avatar';
            avatarEl.replaceWith(img);
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(() => alert('Server error. Please try again.'));
}

// ===================================================================
// ORGANISATION AVATAR / LOGO UPLOAD (school-admin / community-admin)
// ===================================================================
function uploadOrgAvatar(input) {
    const file = input.files[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
        alert('File too large. Max 5MB.');
        return;
    }

    const formData = new FormData();
    formData.append('avatar', file);

    fetch('/update-org-avatar', {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const avatarEl = document.getElementById('org-avatar-img');
            const img = document.createElement('img');
            img.src       = data.avatar_url;
            img.className = 'profile-avatar-large';
            img.id        = 'org-avatar-img';
            img.alt       = 'Org Avatar';
            avatarEl.replaceWith(img);
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(() => alert('Server error. Please try again.'));
}

// ===================================================================
// SETTINGS TOGGLES
// ===================================================================
function toggleSetting(type) {
    // TODO: persist to backend when settings table is added
    const idMap = { email: 'email-notifications', push: 'push-notifications', public: 'public-profile' };
    const checkbox = document.getElementById(idMap[type]);
    if (checkbox) console.log(`${type} notifications ${checkbox.checked ? 'enabled' : 'disabled'}`);
}

// ===================================================================
// CHANGE PASSWORD
// ===================================================================
function changePassword() {
    const current = document.getElementById('current-password').value;
    const newPass = document.getElementById('new-password').value;
    const confirm = document.getElementById('confirm-password').value;

    if (!current || !newPass || !confirm) { alert('Please fill in all password fields.'); return; }
    if (newPass !== confirm) { alert('New passwords do not match.'); return; }
    if (newPass.length < 6) { alert('Password must be at least 6 characters.'); return; }

    fetch('/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ currentPassword: current, newPassword: newPass })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('Password updated successfully.');
            document.getElementById('current-password').value = '';
            document.getElementById('new-password').value     = '';
            document.getElementById('confirm-password').value = '';
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(() => alert('Server error. Please try again.'));
}

// ===================================================================
// DELETE ACCOUNT
// ===================================================================
function deleteAccount() {
    const confirmed   = confirm('Are you absolutely sure you want to delete your account?\n\nThis action cannot be undone.');
    if (!confirmed) return;
    const doubleCheck = confirm('Final confirmation: Delete your account and all associated data?');
    if (!doubleCheck) return;

    fetch('/delete-account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('Account deleted.');
            window.location.href = '/login';
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(() => alert('Server error. Please try again.'));
}

console.log('My Profile loaded successfully.');