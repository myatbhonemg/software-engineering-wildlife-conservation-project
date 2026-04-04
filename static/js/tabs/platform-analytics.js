function signOut() {
    window.location.href = '/logout';
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

console.log('Platform Analytics loaded successfully');