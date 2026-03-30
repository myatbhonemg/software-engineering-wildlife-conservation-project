
// ===== SPECIES LIBRARY JS =====

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
function filterFeed(filter, clickedBtn) {
    // Update active tab
    document.querySelectorAll('.feed-tab').forEach(btn => btn.classList.remove('active'));
    clickedBtn.classList.add('active');

    const userOrgId = document.getElementById('user-data').getAttribute('data-org-id');
    const posts = document.querySelectorAll('.feed-post');

    posts.forEach(post => {
        const postOrg = post.getAttribute('data-org');
        if (filter === 'all') {
            post.style.display = 'block';
        } else {
            post.style.display = (postOrg == userOrgId) ? 'block' : 'none';
        }
    });
}

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

// Toggle Feeds visibility
// Toggle feed visibility
function toggleFeed() {
    const feed = document.getElementById('feed-posts');
    const arrow = document.getElementById('feed-arrow');
    const btn = document.getElementById('feed-toggle-btn');

    feed.classList.toggle('collapsed');
    btn.classList.toggle('collapsed');

    arrow.textContent = feed.classList.contains('collapsed') ? 'View All' : 'Hide All';
}