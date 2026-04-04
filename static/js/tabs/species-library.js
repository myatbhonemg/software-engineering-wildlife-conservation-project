
// ===== SPECIES LIBRARY JS =====

// Sign out function
function signOut() {
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

// Track the current org filter separately
let currentOrgFilter = 'all';

function filterFeed(filter, clickedBtn) {
    document.querySelectorAll('.feed-tab').forEach(btn => btn.classList.remove('active'));
    clickedBtn.classList.add('active');
    currentOrgFilter = filter;
    applyFeedFilters();
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
function toggleFeed() {
    const feed = document.getElementById('feed-posts');
    const controls = document.getElementById('feed-controls');
    const arrow = document.getElementById('feed-arrow');
    const btn = document.getElementById('feed-toggle-btn');

    feed.classList.toggle('collapsed');
    controls.classList.toggle('collapsed');
    btn.classList.toggle('collapsed');

    arrow.textContent = feed.classList.contains('collapsed') ? 'View All' : 'Hide All';
}

function filterFeedPosts() {
    applyFeedFilters();
}

function applyFeedFilters() {
    const search = document.getElementById('feed-search').value.toLowerCase();
    const species = document.getElementById('feed-species-filter').value.toLowerCase();
    const userOrgId = document.getElementById('user-data').getAttribute('data-org-id');
    const posts = document.querySelectorAll('.feed-post');

    posts.forEach(post => {
        const matchesOrg = currentOrgFilter === 'all' || post.dataset.org == userOrgId;
        const matchesSpecies = species === 'all' || post.dataset.species === species;
        const matchesSearch = !search ||
            (post.dataset.location && post.dataset.location.includes(search));

        post.style.display = (matchesOrg && matchesSpecies && matchesSearch) ? 'block' : 'none';
    });
}

// ===== PROGRAMS SECTION =====
let currentProgramOrgFilter = 'all';

function togglePrograms() {
    const posts = document.getElementById('programs-posts');
    const controls = document.getElementById('programs-controls');
    const arrow = document.getElementById('programs-arrow');
    const btn = document.getElementById('programs-toggle-btn');

    posts.classList.toggle('collapsed');
    controls.classList.toggle('collapsed');
    btn.classList.toggle('collapsed');
    arrow.textContent = posts.classList.contains('collapsed') ? 'View All' : 'Hide All';
}

function filterPrograms(filter, clickedBtn) {
    document.querySelectorAll('#programs-posts')
        .forEach(() => {});
    const btns = document.querySelectorAll('.community-feed:nth-of-type(3) .feed-tab');
    btns.forEach(b => b.classList.remove('active'));
    if (clickedBtn) clickedBtn.classList.add('active');
    currentProgramOrgFilter = filter;
    filterProgramPosts();
}

function filterProgramPosts() {
    const search = document.getElementById('programs-search').value.toLowerCase();
    const species = document.getElementById('programs-species-filter').value.toLowerCase();
    const userOrgId = document.getElementById('user-data').getAttribute('data-org-id');
    const posts = document.querySelectorAll('#programs-posts .feed-post');

    posts.forEach(post => {
        const matchesOrg = currentProgramOrgFilter === 'all' || post.dataset.org == userOrgId;
        const matchesSpecies = species === 'all' || post.dataset.species === species;
        const matchesSearch = !search || post.querySelector('h3').textContent.toLowerCase().includes(search)
            || post.querySelector('p').textContent.toLowerCase().includes(search);

        post.style.display = (matchesOrg && matchesSpecies && matchesSearch) ? 'block' : 'none';
    });
}

// ===== CHALLENGES SECTION =====
let currentChallengeOrgFilter = 'all';

function toggleChallenges() {
    const posts = document.getElementById('challenges-posts');
    const controls = document.getElementById('challenges-controls');
    const arrow = document.getElementById('challenges-arrow');
    const btn = document.getElementById('challenges-toggle-btn');

    posts.classList.toggle('collapsed');
    controls.classList.toggle('collapsed');
    btn.classList.toggle('collapsed');
    arrow.textContent = posts.classList.contains('collapsed') ? 'View All' : 'Hide All';
}

function filterChallengesLib(filter, clickedBtn) {
    const btns = document.querySelectorAll('.community-feed:nth-of-type(4) .feed-tab');
    btns.forEach(b => b.classList.remove('active'));
    if (clickedBtn) clickedBtn.classList.add('active');
    currentChallengeOrgFilter = filter;
    filterChallengePosts();
}

function filterChallengePosts() {
    const search = document.getElementById('challenges-search').value.toLowerCase();
    const species = document.getElementById('challenges-species-filter').value.toLowerCase();
    const userOrgId = document.getElementById('user-data').getAttribute('data-org-id');
    const posts = document.querySelectorAll('#challenges-posts .feed-post');

    posts.forEach(post => {
        const matchesOrg = currentChallengeOrgFilter === 'all' || post.dataset.org == userOrgId;
        const matchesSpecies = species === 'all' || post.dataset.species === species;
        const matchesSearch = !search || post.querySelector('h3').textContent.toLowerCase().includes(search)
            || post.querySelector('p').textContent.toLowerCase().includes(search);

        post.style.display = (matchesOrg && matchesSpecies && matchesSearch) ? 'block' : 'none';
    });
}