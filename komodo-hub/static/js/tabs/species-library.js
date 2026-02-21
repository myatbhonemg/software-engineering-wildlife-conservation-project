// ===== SPECIES LIBRARY JS =====

// Check user authentication
const user = JSON.parse(localStorage.getItem('user'));

if (!user) {
    window.location.href = '../login.html';
}

// Update UI with user info
if (user) {
    const navUsername = document.getElementById('nav-username');
    if (navUsername) navUsername.textContent = user.name;

    const roleBadge = document.getElementById('user-role-badge');
    if (roleBadge) {
        const roleNames = {
            'student': 'Student',
            'teacher': 'Teacher',
            'principal': 'Principal',
            'school-admin': 'School Admin',
            'community-member': 'Community',
            'community-admin': 'Community Admin',
            'system-admin': 'System Admin',
            'public': 'Guest'
        };
        roleBadge.textContent = roleNames[user.role] || user.role;
    }
}

const sidebarMenus = {
    'student': `
        <li class="sidebar-item"><a href="../student-dashboard.html">&#127968; Dashboard</a></li>
        <li class="sidebar-item active"><a href="species-library.html">&#128218; Library</a></li>
        <li class="sidebar-item"><a href="#">&#128248; Report Sighting</a></li>
        <li class="sidebar-item"><a href="#">&#127979; My School</a></li>
        <li class="sidebar-item"><a href="#">&#128196; My Programs</a></li>
        <li class="sidebar-item"><a href="#">&#127942; Activity</a></li>
        <li class="sidebar-item"><a href="#">&#127912; Creative Canvas</a></li>
        <li class="sidebar-item"><a href="#">&#128172; Messages</a></li>
        <li class="sidebar-item"><a href="#">&#128100; My Profile</a></li>
    `,
    'teacher': `
        <li class="sidebar-item"><a href="../teacher-dashboard.html">&#127968; Dashboard</a></li>
        <li class="sidebar-item active"><a href="species-library.html">&#128218; Library</a></li>
        <li class="sidebar-item"><a href="#">&#128100; My Students</a></li>
        <li class="sidebar-item"><a href="#">&#128248; Sighting Reports</a></li>
        <li class="sidebar-item"><a href="#">&#127979; Class Programs</a></li>
        <li class="sidebar-item"><a href="#">&#127942; Activity</a></li>
        <li class="sidebar-item"><a href="#">&#127912; Creative Canvas</a></li>
        <li class="sidebar-item"><a href="#">&#128172; Messages</a></li>
        <li class="sidebar-item"><a href="#">&#128100; My Profile</a></li>
    `,
    'principal': `
        <li class="sidebar-item"><a href="../principal-dashboard.html">&#127968; Dashboard</a></li>
        <li class="sidebar-item"><a href="#">&#9989; Approve Students</a></li>
        <li class="sidebar-item"><a href="#">&#128100; Manage Teachers</a></li>
        <li class="sidebar-item"><a href="#">&#127891; Manage Students</a></li>
        <li class="sidebar-item active"><a href="species-library.html">&#128218; Species Library</a></li>
        <li class="sidebar-item"><a href="#">&#128202; School Reports</a></li>
        <li class="sidebar-item"><a href="#">&#128172; Messages</a></li>
        <li class="sidebar-item"><a href="#">&#128100; My Profile</a></li>
    `,

    'school-admin': `
    <li class="sidebar-item"><a href="../school-admin-dashboard.html">&#127968; Dashboard</a></li>
    <li class="sidebar-item active"><a href="species-library.html">&#128218; Library</a></li>
    <li class="sidebar-item"><a href="#">&#127979; School Information</a></li>
    <li class="sidebar-item"><a href="#">&#128100; Manage Teachers</a></li>
    <li class="sidebar-item"><a href="#">&#127891; Manage Students</a></li>
    <li class="sidebar-item"><a href="#">&#128272; Register Members</a></li>
    <li class="sidebar-item"><a href="#">&#128248; Sighting Reports</a></li>
    <li class="sidebar-item"><a href="#">&#128202; School Reports</a></li>
    <li class="sidebar-item"><a href="#">&#128172; Messages</a></li>
    <li class="sidebar-item"><a href="#">&#128100; My Profile</a></li>
`,
'community-member': `
    <li class="sidebar-item"><a href="../community-dashboard.html">&#127968; Dashboard</a></li>
    <li class="sidebar-item active"><a href="species-library.html">&#128218; Library</a></li>
    <li class="sidebar-item"><a href="#">&#128248; Report Sighting</a></li>
    <li class="sidebar-item"><a href="#">&#129309; My Community</a></li>
    <li class="sidebar-item"><a href="#">&#127942; Activity</a></li>
    <li class="sidebar-item"><a href="#">&#127912; Creative Canvas</a></li>
    <li class="sidebar-item"><a href="#">&#128172; Messages</a></li>
    <li class="sidebar-item"><a href="#">&#128100; My Profile</a></li>
`,
'community-admin': `
    <li class="sidebar-item"><a href="../community-admin-dashboard.html">&#127968; Dashboard</a></li>
    <li class="sidebar-item"><a href="#">&#129309; Community Information</a></li>
    <li class="sidebar-item"><a href="#">&#128100; Manage Members</a></li>
    <li class="sidebar-item"><a href="#">&#128272; Register Member</a></li>
    <li class="sidebar-item"><a href="#">&#128248; Sighting Reports</a></li>
    <li class="sidebar-item active"><a href="species-library.html">&#128218; Community Library</a></li>
    <li class="sidebar-item"><a href="#">&#128202; Community Reports</a></li>
    <li class="sidebar-item"><a href="#">&#128172; Messages</a></li>
    <li class="sidebar-item"><a href="#">&#128100; My Profile</a></li>
`,
'system-admin': `
    <li class="sidebar-item"><a href="../system-admin-dashboard.html">&#127968; Dashboard</a></li>
    <li class="sidebar-item"><a href="#">&#127979; Manage Schools</a></li>
    <li class="sidebar-item"><a href="#">&#129309; Manage Communities</a></li>
    <li class="sidebar-item"><a href="#">&#128100; Manage All Users</a></li>
    <li class="sidebar-item active"><a href="species-library.html">&#128218; Library</a></li>
    <li class="sidebar-item"><a href="#">&#128248; All Sighting Reports</a></li>
    <li class="sidebar-item"><a href="#">&#128202; Platform Analytics</a></li>
    <li class="sidebar-item"><a href="#">&#128736; System Settings</a></li>
    <li class="sidebar-item"><a href="#">&#128172; Messages</a></li>
    <li class="sidebar-item"><a href="#">&#128100; My Profile</a></li>
`,
'public': `
    <li class="sidebar-item"><a href="../public-dashboard.html">&#127968; Dashboard</a></li>
    <li class="sidebar-item active"><a href="species-library.html">&#128218; Library</a></li>
    <li class="sidebar-item"><a href="#">&#128248; Sighting Reports</a></li>
`
    
};

document.addEventListener('DOMContentLoaded', function() {
    const sidebarMenu = document.querySelector('.sidebar-menu');
    if (sidebarMenu && user && user.role) {
        sidebarMenu.innerHTML = sidebarMenus[user.role] || sidebarMenus.student;
    }
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

// ===== SPECIES DATABASE FUNCTIONALITY =====

// Search species
const searchInput = document.getElementById('species-search');
if (searchInput) {
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const speciesCards = document.querySelectorAll('.species-card');
        
        speciesCards.forEach(card => {
            const speciesName = card.querySelector('.species-name').textContent.toLowerCase();
            const scientificName = card.querySelector('.species-scientific').textContent.toLowerCase();
            
            if (speciesName.includes(searchTerm) || scientificName.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
}

// Filter by status
const statusFilter = document.getElementById('status-filter');
if (statusFilter) {
    statusFilter.addEventListener('change', function() {
        const filterValue = this.value;
        const speciesCards = document.querySelectorAll('.species-card');
        
        speciesCards.forEach(card => {
            const cardStatus = card.getAttribute('data-status');
            
            if (filterValue === 'all' || cardStatus === filterValue) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
}

// ===== COMMUNITY FEED FUNCTIONALITY =====

// Feed filter tabs
const feedTabs = document.querySelectorAll('.feed-tab');
feedTabs.forEach(tab => {
    tab.addEventListener('click', function() {
        // Remove active from all tabs
        feedTabs.forEach(t => t.classList.remove('active'));
        
        // Add active to clicked tab
        this.classList.add('active');
        
        const filter = this.getAttribute('data-filter');
        
        // For now just show alert, backend will filter posts later
        if (filter === 'school') {
            console.log('Filtering by: My School');
        } else if (filter === 'community') {
            console.log('Filtering by: My Community');
        } else {
            console.log('Showing: All posts');
        }
    });
});

// Load more posts button
console.log('Species Library loaded successfully');
// Toggle species grid visibility
function toggleSpeciesGrid() {
    const grid = document.getElementById('species-grid');
    const controls = document.getElementById('species-controls');
    const arrow = document.getElementById('species-arrow');
    const btn = document.querySelector('.toggle-section-btn');
    
    grid.classList.toggle('collapsed');
    controls.classList.toggle('collapsed');
    btn.classList.toggle('collapsed');
    
    // Change text
    if (grid.classList.contains('collapsed')) {
        arrow.textContent = 'View All';
    } else {
        arrow.textContent = 'Hide All';
    }
}