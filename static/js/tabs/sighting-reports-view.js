// ===== SIGHTING REPORTS VIEW JS =====
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
        feedContainer.style.display = 'grid'; // ← was 'flex'
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
        fetch(`/delete-sighting/${reportId}`, {method: 'POST'})
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                card.remove();
                filterReports();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(() => alert('Server error. Please try again.'));
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