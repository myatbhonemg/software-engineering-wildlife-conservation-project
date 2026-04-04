// ===== MY STUDENTS JS =====

// Check user authentication
const user = JSON.parse(localStorage.getItem('user'));

if (!user) {
    window.location.href = '../login.html';
}


// Update UI with user info
if (user) {
    const navUsername = document.getElementById('nav-username');
    if (navUsername) navUsername.textContent = user.name;
}

// Sidebar menu for teacher
const sidebarMenu = `
    <li class="sidebar-item"><a href="../teacher-dashboard.html">&#127968; Dashboard</a></li>
    <li class="sidebar-item"><a href="species-library.html">&#128218; Library</a></li>
    <li class="sidebar-item active"><a href="my-students.html">&#128100; My Students</a></li>
    <li class="sidebar-item"><a href="sighting-reports-view.html">&#128248; Sighting Reports</a></li>
    <li class="sidebar-item"><a href="programs.html">&#127979; Class Programs</a></li>
    <li class="sidebar-item"><a href="activity.html">&#127942; Activity</a></li>
    <li class="sidebar-item"><a href="creative-canvas.html">&#127912; Creative Canvas</a></li>
    <li class="sidebar-item"><a href="messages.html">&#128172; Messages</a></li>
    <li class="sidebar-item"><a href="my-profile.html">&#128100; My Profile</a></li>
`;

// Load sidebar
document.addEventListener('DOMContentLoaded', function() {
    const sidebarElement = document.querySelector('.sidebar-menu');
    if (sidebarElement) {
        sidebarElement.innerHTML = sidebarMenu;
    }
    
    // Load students
    loadStudents();
});

// Sign out function
function signOut() {
    localStorage.removeItem('user');
    window.location.href = '../login.html';
}

// Toggle sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

// ===== MOCK STUDENT DATA =====
const mockStudents = [
    {
        name: 'Myat Noe',
        email: 'myat@student.edu',
        grade: 10,
        studentId: 'STU-2024-001',
        status: 'Active'
    },
    {
        name: 'Kifo Anderson',
        email: 'kifo@student.edu',
        grade: 10,
        studentId: 'STU-2024-002',
        status: 'Active'
    },
    {
        name: 'Odala Johnson',
        email: 'odala@student.edu',
        grade: 11,
        studentId: 'STU-2024-003',
        status: 'Active'
    },
    {
        name: 'Sarah Williams',
        email: 'sarah@student.edu',
        grade: 9,
        studentId: 'STU-2024-004',
        status: 'Active'
    },
    {
        name: 'Ahmad Putra',
        email: 'ahmad@student.edu',
        grade: 10,
        studentId: 'STU-2024-005',
        status: 'Active'
    },
    {
        name: 'Siti Nurhaliza',
        email: 'siti@student.edu',
        grade: 11,
        studentId: 'STU-2024-006',
        status: 'Active'
    },
    {
        name: 'Budi Santoso',
        email: 'budi@student.edu',
        grade: 9,
        studentId: 'STU-2024-007',
        status: 'Inactive'
    },
    {
        name: 'Dewi Lestari',
        email: 'dewi@student.edu',
        grade: 10,
        studentId: 'STU-2024-008',
        status: 'Active'
    },
    {
        name: 'Rudi Hartono',
        email: 'rudi@student.edu',
        grade: 11,
        studentId: 'STU-2024-009',
        status: 'Active'
    },
    {
        name: 'Nina Fitri',
        email: 'nina@student.edu',
        grade: 9,
        studentId: 'STU-2024-010',
        status: 'Active'
    }
];

// Store original data for search
let allStudents = [...mockStudents];

// ===== LOAD STUDENTS =====
function loadStudents(studentsToShow = mockStudents) {
    const tbody = document.getElementById('students-tbody');
    tbody.innerHTML = '';

    if (studentsToShow.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="empty-state">
                    <div class="empty-state-icon">&#128373;</div>
                    <p>No students found</p>
                </td>
            </tr>
        `;
        return;
    }

    studentsToShow.forEach(student => {
        const row = document.createElement('tr');
        
        // Get first letter for avatar
        const initial = student.name.charAt(0).toUpperCase();
        
        row.innerHTML = `
            <td data-label="Name">
                <div class="student-info">
                    <div class="student-avatar">${initial}</div>
                    <div class="student-details">
                        <span class="student-name">${student.name}</span>
                        <span class="student-email-mobile">${student.email}</span>
                    </div>
                </div>
            </td>
            <td data-label="Email">${student.email}</td>
            <td data-label="Grade">Grade ${student.grade}</td>
            <td data-label="Student ID">${student.studentId}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// ===== SEARCH STUDENTS =====
function searchStudents() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    
    if (searchTerm === '') {
        loadStudents(allStudents);
        return;
    }
    
    const filteredStudents = allStudents.filter(student => {
        return student.name.toLowerCase().includes(searchTerm) ||
               student.email.toLowerCase().includes(searchTerm) ||
               student.studentId.toLowerCase().includes(searchTerm);
    });
    
    loadStudents(filteredStudents);
}

console.log('My Students loaded successfully');