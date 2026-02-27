// ===== PRINCIPAL DASHBOARD JS =====

function signOut() {
    localStorage.removeItem('user');
    window.location.href = '/logout';
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('collapsed');
}

document.querySelectorAll('.coming-soon-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        alert('Coming soon in the next sprint!');
    });
});
