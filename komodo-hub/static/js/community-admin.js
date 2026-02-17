// ===== COMMUNITY ADMIN DASHBOARD JS =====

// Read user from localStorage
const user = JSON.parse(localStorage.getItem('user'));

// If not logged in, redirect to login
if (!user) {
    window.location.href = 'login.html';
}

// If wrong role, redirect to login
if (user && user.role !== 'community-admin') {
    window.location.href = 'login.html';
}

// ===== UPDATE UI WITH USER INFO =====
if (user) {
    const welcomeMsg = document.getElementById('welcome-message');
    if (welcomeMsg) {
        welcomeMsg.textContent = 'Welcome back, ' + user.name + '!';
    }

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

