// student-progress.js
// File: static/js/tabs/student-progress.js

function showTab(name) {
    document.querySelectorAll('.ptab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.ptab').forEach(el => el.classList.remove('active'));
    document.getElementById(`tab-${name}`).classList.add('active');
    event.currentTarget.classList.add('active');
}
function signOut() {
    window.location.href = '/logout';
}
