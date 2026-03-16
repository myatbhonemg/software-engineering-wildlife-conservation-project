// ===== ACTIVITY JS =====

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

    // Show create challenge button for teachers and community admins
    if (user.role === 'teacher' || user.role === 'community-admin') {
        document.getElementById('create-challenge-section').style.display = 'block';
        
        // Hide participant buttons (Accept, In Progress) - they can only view
        document.querySelectorAll('.btn-accept-challenge, .btn-in-progress').forEach(btn => {
            btn.style.display = 'none';
        });
    }

    // Update header description based on role
    const headerDesc = document.getElementById('header-description');
    if (user.role === 'teacher' || user.role === 'community-admin') {
        headerDesc.textContent = 'Create challenges and track participant progress';
    }
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

// ===== FILTER CHALLENGES =====
function filterChallenges(filter) {
    // Update active filter button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-filter') === filter) {
            btn.classList.add('active');
        }
    });

    // Show/hide challenges
    const cards = document.querySelectorAll('.challenge-card');
    cards.forEach(card => {
        const status = card.getAttribute('data-status');
        if (filter === 'all' || status === filter) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// ===== CREATE CHALLENGE MODAL =====
function openCreateChallengeModal() {
    document.getElementById('create-challenge-modal').style.display = 'flex';
}

function closeCreateChallengeModal() {
    document.getElementById('create-challenge-modal').style.display = 'none';
    // Clear form
    document.getElementById('challenge-title').value = '';
    document.getElementById('challenge-description').value = '';
    document.getElementById('challenge-points').value = '';
    document.getElementById('challenge-duration').value = '';
    document.getElementById('challenge-species').value = '';
}

function createChallenge() {
    const title = document.getElementById('challenge-title').value;
    const description = document.getElementById('challenge-description').value;
    const points = document.getElementById('challenge-points').value;
    const duration = document.getElementById('challenge-duration').value;
    const species = document.getElementById('challenge-species').value;

    if (!title || !description || !points || !duration) {
        alert('Please fill in all required fields');
        return;
    }

    // Calculate deadline
    const now = new Date();
    const deadline = new Date(now.getTime() + (duration * 24 * 60 * 60 * 1000));
    
    // Create challenge object
    const newChallenge = {
        id: Date.now(),
        title: title,
        description: description,
        points: points,
        duration: duration,
        species: species,
        creator: user.name,
        createdDate: now.toISOString(),
        deadline: deadline.toISOString(),
        status: 'active',
        participants: 0
    };

    // Get existing challenges from localStorage
    let challenges = JSON.parse(localStorage.getItem('challenges')) || [];
    challenges.unshift(newChallenge); // Add to beginning
    localStorage.setItem('challenges', JSON.stringify(challenges));

    alert(`Challenge "${title}" created successfully!\n\nPoints: ${points}\nDuration: ${duration} days\nDeadline: ${deadline.toLocaleDateString()}`);
    closeCreateChallengeModal();

    // Reload page to show new challenge
    location.reload();
}

// Load challenges from localStorage and check expiry
document.addEventListener('DOMContentLoaded', function() {
    checkExpiredChallenges();
});

function checkExpiredChallenges() {
    let challenges = JSON.parse(localStorage.getItem('challenges')) || [];
    const now = new Date();
    let updated = false;

    challenges = challenges.map(challenge => {
        if (challenge.status === 'active' && new Date(challenge.deadline) < now) {
            challenge.status = 'expired';
            updated = true;
        }
        return challenge;
    });

    if (updated) {
        localStorage.setItem('challenges', JSON.stringify(challenges));
    }
}

// ===== CHALLENGE ACTIONS =====
function acceptChallenge(challengeId) {
    const confirmAccept = confirm('Accept this challenge?\n\nYou will have until the deadline to complete it.');
    
    if (confirmAccept) {
        alert('Challenge accepted! Good luck! 🎯');
        // TODO: Update backend and UI
        console.log('Accepted challenge:', challengeId);
    }
}

function viewProgress(challengeId) {
    alert('Challenge Progress\n\nYou are currently working on this challenge.\n\n[Feature coming soon: View detailed progress, upload evidence, and submit completion]');
    console.log('Viewing progress for challenge:', challengeId);
}

function viewSubmission(challengeId) {
    alert('Your Submission\n\nCompleted on Feb 25, 2026\nPoints earned: +40\n\n[Feature coming soon: View your submission details, photos, and feedback]');
    console.log('Viewing submission for challenge:', challengeId);
}

function viewResults(challengeId) {
    alert('Challenge Results\n\nThis challenge has ended.\n\n[Feature coming soon: See winner, top submissions, and leaderboard]');
    console.log('Viewing results for challenge:', challengeId);
}

console.log('Activity loaded successfully');