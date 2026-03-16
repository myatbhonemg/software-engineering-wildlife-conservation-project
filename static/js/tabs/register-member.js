// ===== REGISTER MEMBER JS =====

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

// ===== FORM HANDLING =====

// Handle form submission
document.getElementById('registration-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Get form values
    firstName = document.getElementById('first-name').value;
    lastName = document.getElementById('last-name').value;
    const formData = {
        role: document.getElementById('member-role').value,
        email: document.getElementById('email').value,
        accessCode: null
    };
    formData.fullName = firstName + lastName;

    // Add role-specific fields
    if (formData.role === 'student') {
        code = Math.floor(Math.random() * 900) + 100;
        formData.accessCode = firstName + code;
    }

    fetch('/register-member', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(formData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Success message
            const roleLabel = {
                'student': 'Student',
                'teacher': 'Teacher',
                'community-member': 'Community Member'
            }[formData.role];
            alert(`✅ Registration Request Submitted!\n\n${firstName} ${lastName} (${roleLabel})\n\nEmail: ${formData.email}\n\nThe system will verify if this email is registered. If verified, an access code will be sent to complete the registration process.`);
            resetForm();
        }else{
            alert('Error: ' + (data.message || 'Registration failed'));
        }
    })
    .catch(() => alert('Server error. Please try again'))

    // TODO: Send to backend to check if email is registered
    console.log('Registering member:', formData);




    // Reset form
    resetForm();
});

// Reset form
function resetForm() {
    document.getElementById('registration-form').reset();
    document.querySelectorAll('.student-fields, .teacher-fields, .community-fields').forEach(section => {
        section.style.display = 'none';
    });
}

console.log('Register Member loaded successfully');