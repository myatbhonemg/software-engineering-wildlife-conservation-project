// ===== SIGHTING REPORTS VIEW JS =====

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
            'teacher': 'Teacher',
            'principal': 'Principal',
            'school-admin': 'School Admin',
            'community-admin': 'Community Admin',
            'system-admin': 'System Admin'
        };
        roleBadge.textContent = roleNames[user.role] || user.role;
    }

    // Update header description based on role
    const headerDesc = document.getElementById('header-description');
    if (headerDesc) {
        const descriptions = {
            'teacher': 'View and manage sighting reports from your students',
            'principal': 'View all sighting reports from your school',
            'school-admin': 'View and manage all school sighting reports',
            'community-admin': 'View all sighting reports from your community',
            'system-admin': 'View all sighting reports across the platform'
        };
        headerDesc.textContent = descriptions[user.role] || 'View sighting reports';
    }
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

// ===== FILTER REPORTS =====

function filterReports() {
    const speciesFilter = document.getElementById('filter-species').value;
    const searchFilter = document.getElementById('filter-search').value.toLowerCase();

    const cards = document.querySelectorAll('.report-card');
    let visibleCount = 0;

    cards.forEach(card => {
        const species = card.getAttribute('data-species');
        const location = card.getAttribute('data-location');
        const reporter = card.getAttribute('data-reporter');

        // Check filters
        const speciesMatch = (speciesFilter === 'all' || species === speciesFilter);
        const searchMatch = (searchFilter === '' || location.includes(searchFilter) || reporter.includes(searchFilter));

        if (speciesMatch && searchMatch) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    // Show/hide no results message
    const noResults = document.getElementById('no-results');
    const feedContainer = document.getElementById('reports-feed');
    
    if (visibleCount === 0) {
        noResults.style.display = 'block';
        feedContainer.style.display = 'none';
    } else {
        noResults.style.display = 'none';
        feedContainer.style.display = 'flex';
    }
}

// ===== RESET FILTERS =====

function resetFilters() {
    document.getElementById('filter-species').value = 'all';
    document.getElementById('filter-search').value = '';
    filterReports();
}

// ===== DELETE REPORT =====

function deleteReport(button, reportId) {
    const card = button.closest('.report-card');
    const reporterName = card.querySelector('.user-name').textContent;
    const title = card.querySelector('h3').textContent;
    
    if (confirm(`Delete this sighting report?\n\n${title}\nReported by: ${reporterName}`)) {
        // Remove the card
        card.remove();
        
        alert('Report deleted successfully');
        
        // TODO: Send delete request to backend
        // fetch('/api/sightings/' + reportId, { method: 'DELETE' })
        
        console.log('Deleted report:', reportId);
        
        // Re-run filter to update "no results" message if needed
        filterReports();
    }
}

// ===== VIEW PHOTO =====

function viewPhoto(photoUrl) {
    // Open photo in new tab
    window.open(photoUrl, '_blank');
    
    // Alternative: Could create a modal/lightbox here
    // For now, simple new tab is clean and functional
}

console.log('Sighting Reports View loaded successfully');