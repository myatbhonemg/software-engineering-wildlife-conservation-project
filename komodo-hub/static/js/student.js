// ===== STUDENT DASHBOARD JS =====

// Read user from localStorage (set during login)
const user = JSON.parse(localStorage.getItem('user'));

// If not logged in, redirect back to login
if (!user) {
    window.location.href = 'login.html';
}

// If wrong role, redirect back to login
if (user && user.role !== 'student') {
    window.location.href = 'login.html';
}

// ===== UPDATE UI WITH USER INFO =====
if (user) {
    // Update welcome message
    const welcomeMsg = document.getElementById('welcome-message');
    if (welcomeMsg) {
        welcomeMsg.textContent = 'Welcome back, ' + user.name + '!';
    }

    // Update nav username
    const navUsername = document.getElementById('nav-username');
    if (navUsername) {
        navUsername.textContent = user.name;
    }
}

// ===== SIGN OUT =====
function signOut() {
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

// ===== SIDEBAR TOGGLE =====
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}