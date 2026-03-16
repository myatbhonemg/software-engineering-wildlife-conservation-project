// ===== MANAGE USERS JS =====

// Check user authentication
const user = JSON.parse(localStorage.getItem('user'));

if (!user) {
    window.location.href = '../login.html';
}

// Determine management type from URL parameter
const urlParams = new URLSearchParams(window.location.search);
const manageType = urlParams.get('type') || 'users';

// Update UI with user info
if (user) {
    const navUsername = document.getElementById('nav-username');
    if (navUsername) navUsername.textContent = user.name;

    const roleBadge = document.getElementById('user-role-badge');
    if (roleBadge) {
        const roleNames = {
            'teacher': 'Teacher',
            'principal': 'Principal',
            'school-admin': 'School Admin',
            'community-admin': 'Community Admin',
            'system-admin': 'System Admin'
        };
        roleBadge.textContent = roleNames[user.role] || user.role;
    }

    // Update page title and description based on management type
    updatePageContent();
}

// Update page content based on what's being managed
function updatePageContent() {
    const pageTitle = document.getElementById('page-title');
    const pageDescription = document.getElementById('page-description');
    const statLabel1 = document.getElementById('stat-label-1');
    const colHeader2 = document.getElementById('col-header-2');
    const colHeader3 = document.getElementById('col-header-3');

    const contentMap = {
        'teachers': {
            title: '&#128100; Manage Teachers',
            description: 'View and manage teacher accounts',
            statLabel: 'Total Teachers',
            col2: 'Email',
            col3: 'Subject',
            showRoleFilter: false
        },
        'students': {
            title: '&#127891; Manage Students',
            description: 'View and manage student accounts',
            statLabel: 'Total Students',
            col2: 'Email',
            col3: 'Grade',
            showRoleFilter: false
        },
        'members': {
            title: '&#128100; Manage Members',
            description: 'View and manage community member accounts',
            statLabel: 'Total Members',
            col2: 'Email',
            col3: 'Role',
            showRoleFilter: false
        },
        'schools': {
            title: '&#127979; Manage Schools',
            description: 'View and manage registered schools',
            statLabel: 'Total Schools',
            col2: 'Location',
            col3: 'Members',
            showRoleFilter: false
        },
        'communities': {
            title: '&#129309; Manage Communities',
            description: 'View and manage registered communities',
            statLabel: 'Total Communities',
            col2: 'Location',
            col3: 'Members',
            showRoleFilter: false
        },
        'all-users': {
            title: '&#128100; Manage All Users',
            description: 'View and manage all platform users',
            statLabel: 'Total Users',
            col2: 'Email',
            col3: 'Role',
            showRoleFilter: true
        }
    };

    const content = contentMap[manageType] || contentMap['all-users'];
    
    pageTitle.innerHTML = content.title;
    pageDescription.textContent = content.description;
    statLabel1.textContent = content.statLabel;
    colHeader2.textContent = content.col2;
    colHeader3.textContent = content.col3;

    // Show/hide role filter
    if (content.showRoleFilter) {
        document.getElementById('role-filter-group').style.display = 'block';
    }
}

// Update sidebar active state based on current page type
function updateSidebarActive() {
    const sidebarItems = document.querySelectorAll('.sidebar-item');
    
    // Remove all active classes first
    sidebarItems.forEach(item => item.classList.remove('active'));
    
    // Find and activate the correct item based on manage type
    sidebarItems.forEach(item => {
        const link = item.querySelector('a');
        if (link) {
            const href = link.getAttribute('href');
            // Check if the link contains the EXACT type parameter
            if (href && href.includes(`?type=${manageType}`)) {
                item.classList.add('active');
            }
        }
    });
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

// ===== MOCK DATA LOADING =====
function loadMockData() {
    const tbody = document.getElementById('users-tbody');
    
    const mockData = {
        'teachers': [
            { name: 'Mr. Tevin Rodriguez', email: 'tevin@school.edu', subject: 'Biology', joined: 'Jan 2024', status: 'active', avatar: '👨‍🏫' },
            { name: 'Ms. Sarah Johnson', email: 'sarah@school.edu', subject: 'Environmental Science', joined: 'Mar 2024', status: 'active', avatar: '👩‍🏫' },
            { name: 'Dr. Mike Anderson', email: 'mike@school.edu', subject: 'Chemistry', joined: 'Sep 2023', status: 'active', avatar: '👨‍🏫' },
            { name: 'Mrs. Lisa Wong', email: 'lisa@school.edu', subject: 'Physics', joined: 'Feb 2024', status: 'inactive', avatar: '👩‍🏫' }
        ],
        'students': [
            { name: 'Myat Noe', email: 'myat@student.edu', grade: '10', joined: 'Sep 2025', status: 'active', avatar: '👨‍🎓' },
            { name: 'Kifo Chen', email: 'kifo@student.edu', grade: '11', joined: 'Sep 2025', status: 'active', avatar: '👩‍🎓' },
            { name: 'Odala Kim', email: 'odala@student.edu', grade: '9', joined: 'Sep 2025', status: 'active', avatar: '👨‍🎓' },
            { name: 'Emily Tan', email: 'emily@student.edu', grade: '12', joined: 'Sep 2024', status: 'active', avatar: '👩‍🎓' },
            { name: 'David Lee', email: 'david@student.edu', grade: '10', joined: 'Sep 2025', status: 'inactive', avatar: '👨‍🎓' }
        ],
        'members': [
            { name: 'Ahmad Putra', email: 'ahmad@community.org', role: 'Volunteer', joined: 'Nov 2025', status: 'active', avatar: '👨‍💼' },
            { name: 'Siti Nurhaliza', email: 'siti@community.org', role: 'Member', joined: 'Dec 2025', status: 'active', avatar: '👩‍💼' },
            { name: 'Budi Santoso', email: 'budi@community.org', role: 'Activist', joined: 'Oct 2025', status: 'active', avatar: '👨‍💼' }
        ],
        'schools': [
            { name: 'Jakarta International School', location: 'Jakarta', members: '450', joined: 'Jan 2024', status: 'active', avatar: '🏫' },
            { name: 'Bali Green School', location: 'Bali', members: '320', joined: 'Mar 2024', status: 'active', avatar: '🏫' },
            { name: 'Surabaya Conservation Academy', location: 'Surabaya', members: '280', joined: 'Feb 2024', status: 'active', avatar: '🏫' }
        ],
        'communities': [
            { name: 'Ujung Kulon Conservation Group', location: 'West Java', members: '85', joined: 'Feb 2024', status: 'active', avatar: '🌳' },
            { name: 'Sumatra Wildlife Watchers', location: 'Sumatra', members: '120', joined: 'Jan 2024', status: 'active', avatar: '🌳' },
            { name: 'Bali Bird Protectors', location: 'Bali', members: '65', joined: 'Mar 2024', status: 'active', avatar: '🌳' }
        ],
        'all-users': [
            { name: 'Mr. Tevin Rodriguez', email: 'tevin@school.edu', role: 'Teacher', joined: 'Jan 2024', status: 'active', avatar: '👨‍🏫' },
            { name: 'Myat Noe', email: 'myat@student.edu', role: 'Student', joined: 'Sep 2025', status: 'active', avatar: '👨‍🎓' },
            { name: 'Ahmad Putra', email: 'ahmad@community.org', role: 'Community', joined: 'Nov 2025', status: 'active', avatar: '👨‍💼' }
        ]
    };

    const data = mockData[manageType] || mockData['all-users'];
    
    data.forEach((item, index) => {
        const row = document.createElement('tr');
        row.setAttribute('data-status', item.status);
        row.setAttribute('data-search', `${item.name} ${item.email}`.toLowerCase());
        
        const col3Value = item.subject || item.grade || item.role || item.members || '';
        
        row.innerHTML = `
            <td>
                <div class="user-cell">
                    <div class="user-avatar">${item.avatar}</div>
                    <div class="user-info">
                        <div class="user-name">${item.name}</div>
                        <div class="user-id">${item.email || item.location}</div>
                    </div>
                </div>
            </td>
            <td>${item.email || item.location}</td>
            <td>${col3Value}</td>
            <td>${item.joined}</td>
            <td><span class="status-badge status-${item.status}">${item.status === 'active' ? 'Active' : 'Inactive'}</span></td>
            <td>
                <div class="action-buttons">
                    <button class="btn-edit-user" onclick="editUser(${index})">Edit</button>
                    <button class="btn-delete-user" onclick="deleteUser(${index})">Delete</button>
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// ===== FILTER USERS =====
function filterUsers() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const statusFilter = document.getElementById('filter-status').value;
    const roleFilter = document.getElementById('filter-role') ? document.getElementById('filter-role').value : 'all';
    
    const rows = document.querySelectorAll('#users-tbody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const searchText = row.getAttribute('data-search');
        const status = row.getAttribute('data-status');
        
        const matchesSearch = searchText.includes(searchTerm);
        const matchesStatus = statusFilter === 'all' || status === statusFilter;
        
        if (matchesSearch && matchesStatus) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Show/hide no results message
    const noResults = document.getElementById('no-results');
    const tableContainer = document.querySelector('.users-table-container');
    
    if (visibleCount === 0) {
        noResults.style.display = 'block';
        tableContainer.style.display = 'none';
    } else {
        noResults.style.display = 'none';
        tableContainer.style.display = 'block';
    }
}

// ===== USER ACTIONS =====
function editUser(index) {
    // TODO: Load user data into modal
    document.getElementById('edit-user-modal').style.display = 'flex';
    console.log('Editing user:', index);
}

function closeEditModal() {
    document.getElementById('edit-user-modal').style.display = 'none';
}

function saveUser() {
    const name = document.getElementById('edit-name').value;
    const email = document.getElementById('edit-email').value;
    
    // TODO: Save to backend
    alert(`User updated!\n\nName: ${name}\nEmail: ${email}`);
    closeEditModal();
}

function deleteUser(index) {
    const confirmDelete = confirm('Are you sure you want to delete this user?\n\nThis action cannot be undone.');
    
    if (confirmDelete) {
        alert('User deleted successfully');
        // TODO: Delete from backend and refresh list
        console.log('Deleting user:', index);
    }
}

function exportUsers() {
    alert('Exporting users to CSV...\n\n[Feature coming soon]');
    // TODO: Generate CSV export
}

console.log('Manage Users loaded - Type:', manageType);