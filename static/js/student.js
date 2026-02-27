// ===== STUDENT DASHBOARD JS =====

// ===== SIGN OUT =====
function signOut() {
    localStorage.removeItem('user');
    window.location.href = '/logout';
}

// ===== SIDEBAR TOGGLE =====
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}