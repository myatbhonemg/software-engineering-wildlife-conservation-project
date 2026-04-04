// ===== CLASSES JS =====

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

function signOut() {
    window.location.href = '/logout';
}

let currentClassId = null;
let enrolledStudents = [];
let availableStudents = [];

// ===== CREATE CLASS =====
function openCreateClassModal() {
    document.getElementById('create-class-modal').style.display = 'flex';
}

function closeCreateClassModal() {
    document.getElementById('create-class-modal').style.display = 'none';
    document.getElementById('class-name').value = '';
    document.getElementById('class-subject').value = '';
    document.getElementById('class-teacher').value = '';
}

function createClass() {
    const name    = document.getElementById('class-name').value.trim();
    const subject = document.getElementById('class-subject').value.trim();
    const teacher = document.getElementById('class-teacher').value;

    if (!name) { alert('Please enter a class name.'); return; }

    fetch('/create-class', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, subject, teacher_id: teacher || null })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            closeCreateClassModal();
            location.reload();
        } else {
            alert(data.message || 'Failed to create class.');
        }
    });
}

// ===== DELETE CLASS =====
function deleteClass(classId) {
    if (!confirm('Delete this class? Students will be unenrolled but their accounts remain.')) return;

    fetch(`/delete-class/${classId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const card = document.getElementById(`class-card-${classId}`);
            if (card) card.remove();

            // Show empty state if no cards left
            const grid = document.getElementById('classes-grid');
            if (!grid.querySelector('.class-card')) {
                grid.innerHTML = `<div class="no-classes"><p>No classes yet. Create your first one!</p></div>`;
            }
        } else {
            alert(data.message || 'Could not delete class.');
        }
    });
}

// ===== UPDATE TEACHER =====
function updateTeacher(classId, teacherId) {
    fetch(`/update-class-teacher/${classId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ teacher_id: teacherId || null })
    })
    .then(r => r.json())
    .then(data => {
        if (!data.success) alert(data.message || 'Could not update teacher.');
    });
}

// ===== MANAGE STUDENTS MODAL =====
function openStudentsModal(classId, className) {
    currentClassId = classId;
    document.getElementById('students-modal-title').textContent = `Students — ${className}`;
    document.getElementById('students-modal').style.display = 'flex';
    loadClassStudents(classId);
}

function closeStudentsModal() {
    document.getElementById('students-modal').style.display = 'none';
    currentClassId = null;
    enrolledStudents = [];
    availableStudents = [];
    document.getElementById('student-search').value = '';
}

function loadClassStudents(classId) {
    document.getElementById('enrolled-list').innerHTML = '<p class="loading-text">Loading...</p>';
    document.getElementById('available-list').innerHTML = '<p class="loading-text">Loading...</p>';

    fetch(`/get-class-students/${classId}`)
    .then(r => r.json())
    .then(data => {
        if (!data.success) return;
        enrolledStudents = data.enrolled;
        availableStudents = data.available;
        renderEnrolled();
        renderAvailable(availableStudents);
    });
}

function renderEnrolled() {
    const list = document.getElementById('enrolled-list');
    document.getElementById('enrolled-count').textContent = enrolledStudents.length;

    if (enrolledStudents.length === 0) {
        list.innerHTML = '<p class="empty-list-text">No students in this class yet.</p>';
        return;
    }

    list.innerHTML = enrolledStudents.map(s => `
        <div class="student-item" id="enrolled-${s.user_id}">
            <div class="student-item-top">
                <div class="student-avatar">
                    ${s.avatar
                        ? `<img src="/static/${s.avatar}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`
                        : '👤'}
                </div>
                <div class="student-info">
                    <span class="student-name">${s.fullname}</span>
                    <span class="student-email">${s.email}</span>
                </div>
                <button class="btn-student-action btn-remove"
                        onclick="removeStudent(${s.user_id}, '${s.fullname}')">
                    Remove
                </button>
            </div>
            <div class="student-item-actions">
                <a href="/student-progress/${s.user_id}" class="btn-student-nav btn-progress">📊 Progress</a>
                <a href="/student-submissions/${s.user_id}" class="btn-student-nav btn-submissions">📋 Submissions</a>
                <a href="/messages?open=${s.user_id}" class="btn-student-nav btn-message">💬 Message</a>
            </div>
        </div>
    `).join('');
}

function renderAvailable(students) {
    const list = document.getElementById('available-list');
    document.getElementById('available-count').textContent = availableStudents.length;

    if (students.length === 0) {
        list.innerHTML = '<p class="empty-list-text">No available students.</p>';
        return;
    }

    list.innerHTML = students.map(s => `
        <div class="student-item" id="available-${s.user_id}">
            <div class="student-avatar">
                ${s.avatar
                    ? `<img src="/static/${s.avatar}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`
                    : '👤'}
            </div>
            <div class="student-info">
                <span class="student-name">${s.fullname}</span>
                <span class="student-email">${s.email}</span>
            </div>
            <button class="btn-student-action btn-add"
                    onclick="addStudent(${s.user_id}, '${s.fullname}')">
                + Add
            </button>
        </div>
    `).join('');
}

function filterStudents(query) {
    const filtered = query.trim()
        ? availableStudents.filter(s =>
            s.fullname.toLowerCase().includes(query.toLowerCase()) ||
            s.email.toLowerCase().includes(query.toLowerCase())
          )
        : availableStudents;
    renderAvailable(filtered);
}

function addStudent(studentId, name) {
    fetch(`/add-to-class/${currentClassId}/${studentId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (!data.success) { alert(data.message); return; }

        // Move from available to enrolled
        const student = availableStudents.find(s => s.user_id === studentId);
        if (student) {
            availableStudents = availableStudents.filter(s => s.user_id !== studentId);
            enrolledStudents.push(student);
            renderEnrolled();
            renderAvailable(availableStudents);
            updateCardStudentCount(1);
        }
    });
}

function removeStudent(studentId, name) {
    fetch(`/remove-from-class/${currentClassId}/${studentId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (!data.success) { alert(data.message); return; }

        // Move from enrolled to available
        const student = enrolledStudents.find(s => s.user_id === studentId);
        if (student) {
            enrolledStudents = enrolledStudents.filter(s => s.user_id !== studentId);
            availableStudents.push(student);
            availableStudents.sort((a, b) => a.fullname.localeCompare(b.fullname));
            renderEnrolled();
            renderAvailable(availableStudents);
            updateCardStudentCount(-1);
        }
    });
}

function updateCardStudentCount(delta) {
    const card = document.getElementById(`class-card-${currentClassId}`);
    if (!card) return;
    const statEl = card.querySelector('.class-stat strong');
    if (statEl) statEl.textContent = parseInt(statEl.textContent) + delta;
}
document.getElementById('students-modal').addEventListener('click', function (e) {
    if (e.target === this) closeStudentsModal();
});

console.log('Classes loaded successfully');