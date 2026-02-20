const user = JSON.parse(localStorage.getItem('user'));

if (!user) {
    window.location.href = 'login.html';
}

if (user && user.role !== 'system-admin') {
    window.location.href = 'login.html';
}

if (user) {
    const welcomeMsg = document.getElementById('welcome-message');
    if (welcomeMsg) welcomeMsg.textContent = 'Welcome back, ' + user.name + '!';

    const navUsername = document.getElementById('nav-username');
    if (navUsername) navUsername.textContent = user.name;
}

function signOut() {
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('collapsed');
}

document.querySelectorAll('.coming-soon-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        alert('Coming soon in the next sprint!');
    });
});

document.querySelectorAll('.sidebar-item:not(.active) a').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        alert('Coming soon in the next sprint!');
    });
});