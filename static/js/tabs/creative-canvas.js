// ===== CREATIVE CANVAS JS =====

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

// ===== DRAG AND DROP =====
function setupDragDrop() {
    const uploadZone = document.getElementById('upload-zone');

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        handleFiles(files);
    });
}

// ===== FILE HANDLING =====
function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    const maxSize = 25 * 1024 * 1024; // 25MB
    const allowedTypes = [
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/pdf',
        'text/plain',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];

    for (let file of files) {
        // Check file size
        if (file.size > maxSize) {
            alert(`File "${file.name}" is too large. Maximum size is 25MB.`);
            continue;
        }

        // Check file type
        if (!allowedTypes.includes(file.type) && !file.name.match(/\.(ppt|pptx|doc|docx|pdf|txt|xls|xlsx)$/i)) {
            alert(`File "${file.name}" is not a supported format.`);
            continue;
        }

        // Upload file
        uploadFile(file);
    }

    // Clear input
    document.getElementById('file-input').value = '';
}

function uploadFile(file) {
    // TODO: Upload to backend
    console.log('Uploading file:', file.name);
    
    alert(`File "${file.name}" uploaded successfully!\n\nSize: ${(file.size / 1024 / 1024).toFixed(2)} MB`);
    
    // In real app, this would:
    // 1. Show upload progress
    // 2. Send to backend
    // 3. Add to files grid
}

// ===== FILTER FILES =====
function filterFiles(filter) {
    // Update active tab
    document.querySelectorAll('.canvas-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.getAttribute('data-filter') === filter) {
            tab.classList.add('active');
        }
    });

    // Show/hide files
    const cards = document.querySelectorAll('.file-card');
    let visibleCount = 0;

    cards.forEach(card => {
        const type = card.getAttribute('data-type');
        const owner = card.getAttribute('data-owner');

        let show = false;

        if (filter === 'all') {
            show = true;
        } else if (filter === 'my-files') {
            show = owner === 'mine';
        } else {
            show = type === filter;
        }

        if (show) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    // Show no results message
    const noResults = document.getElementById('no-results');
    const filesGrid = document.getElementById('files-grid');

    if (visibleCount === 0) {
        noResults.style.display = 'block';
        filesGrid.style.display = 'none';
    } else {
        noResults.style.display = 'none';
        filesGrid.style.display = 'grid';
    }
}

// ===== FILE ACTIONS =====
function downloadFile(fileId) {
    alert('Downloading file...\n\n[Feature coming soon: Download file to your device]');
    console.log('Downloading file:', fileId);
    // TODO: Implement actual download
}

function viewFile(fileId) {
    alert('Opening file viewer...\n\n[Feature coming soon: View file in browser]');
    console.log('Viewing file:', fileId);
    // TODO: Open file viewer modal
}

function deleteFile(fileId) {
    const confirmDelete = confirm('Are you sure you want to delete this file?\n\nThis action cannot be undone.');
    
    if (confirmDelete) {
        alert('File deleted successfully');
        console.log('Deleted file:', fileId);
        // TODO: Remove from backend and UI
    }
}

console.log('Creative Canvas loaded successfully');