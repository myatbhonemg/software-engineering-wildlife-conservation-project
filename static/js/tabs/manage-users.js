// ===== MANAGE USERS JS =====
updatePageContent();
updateSidebarActive();

// Update page content based on what's being managed
function updatePageContent() {
    const pageTitle = document.getElementById('page-title');
    const pageDescription = document.getElementById('page-description');
    const statLabel1 = document.getElementById('stat-label-1');
    const colHeader2 = document.getElementById('col-header-2');
    const colHeader3 = document.getElementById('col-header-3');

    const contentMap = {
        'staff': {
            title: '&#128188; Manage Staff',
            description: 'View and manage teachers and principals',
            statLabel: 'Total Staff',
            col2: 'Email',
            col3: 'Role',
            showRoleFilter: false
        },
        'students': {
            title: '&#127891; Manage Students',
            description: 'View and manage student accounts',
            statLabel: 'Total Students',
            col2: 'Email',
            col3: 'Role',
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

// ===== ADD MEMBER MODAL =====
function openAddMemberModal() {
    const type = manageType;
    const titleMap = {
        'staff': 'Add Staff Member',
        'students': 'Add Student',
        'members': 'Add Community Member'
    };
    document.getElementById('add-member-title').textContent = titleMap[type] || 'Add Member';
    document.getElementById('add-member-modal').style.display = 'flex';
    generateCode(); // Auto-generate a code on open
}

function closeAddMemberModal() {
    document.getElementById('add-member-modal').style.display = 'none';
    document.getElementById('add-name').value = '';
    document.getElementById('add-email').value = '';
    document.getElementById('add-code').value = '';
}

function generateCode() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let code = '';
    for (let i = 0; i < 8; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    document.getElementById('add-code').value = code;
}

function submitAddMember() {
    const roleEl = document.getElementById('add-role');
    const role      = roleEl.tagName === 'SELECT' ? roleEl.value : roleEl.value;
    const full_name = document.getElementById('add-name').value.trim();
    const email     = document.getElementById('add-email').value.trim();
    const access_code = document.getElementById('add-code').value.trim();

    if (!full_name || !email || !access_code) {
        alert('Please fill in all fields.');
        return;
    }
    
    //Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert('Please enter a valid email address.');
        return;
    }

    fetch('/add-member', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, full_name, email, access_code })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            closeAddMemberModal();
            // Show the access code in a clear alert so admin can copy it
            alert(`✅ Invitation created!\n\nName: ${full_name}\nEmail: ${email}\nAccess Code: ${access_code}\n\nShare this code with them to complete registration.`);
            location.reload();
        } else {
            alert(data.message || 'Failed to create invitation.');
        }
    });
}

// ===== REVOKE INVITATION =====
function revokeInvitation(regId) {
    if (!confirm('Revoke this invitation? The access code will no longer work.')) return;

    fetch(`/revoke-invitation/${regId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const row = document.getElementById(`pending-row-${regId}`);
            if (row) row.remove();
        } else {
            alert(data.message || 'Could not revoke invitation.');
        }
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
function editUser(userId, name, email, status) {
    document.getElementById('edit-user-modal').setAttribute('data-user-id', userId);
    document.getElementById('edit-name').value = name;
    document.getElementById('edit-email').value = email;
    document.getElementById('edit-status').value = status;
    document.getElementById('edit-user-modal').style.display = 'flex';
}

function closeEditModal() {
    document.getElementById('edit-user-modal').style.display = 'none';
}

function saveUser() {
    const userId = document.getElementById('edit-user-modal').getAttribute('data-user-id');
    const status = document.getElementById('edit-status').value;

    fetch('/update-user-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, status: status })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('User status updated successfully');
            closeEditModal();
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    });
}

function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?\n\nThis action cannot be undone.')) return;

    fetch(`/delete-user/${userId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('User deleted successfully');
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    });
}

function toggleExportMenu() {
    const menu = document.getElementById('export-menu');
    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

// Close menu if clicked outside
document.addEventListener('click', function(e) {
    const menu = document.getElementById('export-menu');
    if (!e.target.closest('.controls-right')) {
        menu.style.display = 'none';
    }
});

function getVisibleRows() {
    // Only export rows currently visible (respects active filters)
    return [...document.querySelectorAll('#users-tbody tr')]
        .filter(row => row.style.display !== 'none' && row.getAttribute('data-status'));
}

function exportCSV() {
    document.getElementById('export-menu').style.display = 'none';

    const headers = ['Name', 'Email', 'Role', 'Joined Date', 'Status'];
    const rows = getVisibleRows();

    const csvLines = [headers.join(',')];

    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const name = cells[0].querySelector('.user-name')?.textContent.trim() || '';
        const email = cells[1].textContent.trim();
        const role = cells[2].textContent.trim();
        const joined = cells[3].textContent.trim();
        const status = cells[4].textContent.trim();
        // Wrap in quotes to handle commas in names
        csvLines.push([`"${name}"`, `"${email}"`, `"${role}"`, `"${joined}"`, `"${status}"`].join(','));
    });

    const blob = new Blob([csvLines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${manageType}-export.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

function exportPDF() {
    document.getElementById('export-menu').style.display = 'none';

    const rows = getVisibleRows();
    const title = document.getElementById('page-title').textContent;

    // Build a printable HTML page
    const printContent = `
        <html>
        <head>
            <title>${title}</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 32px; color: #222; }
                h1 { font-size: 22px; margin-bottom: 4px; }
                p { color: #666; font-size: 13px; margin-bottom: 20px; }
                table { width: 100%; border-collapse: collapse; font-size: 13px; }
                th { background: #2d6a4f; color: white; padding: 10px 12px; text-align: left; }
                td { padding: 9px 12px; border-bottom: 1px solid #eee; }
                tr:nth-child(even) td { background: #f9f9f9; }
                .badge { padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }
                .active { background: #d4edda; color: #1a6b35; }
                .inactive { background: #f8d7da; color: #842029; }
            </style>
        </head>
        <body>
            <h1>${title}</h1>
            <p>Exported on ${new Date().toLocaleDateString('en-GB', { day:'numeric', month:'long', year:'numeric' })}</p>
            <table>
                <thead>
                    <tr>
                        <th>Name</th><th>Email</th><th>Role</th><th>Joined Date</th><th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(row => {
                        const cells = row.querySelectorAll('td');
                        const name = cells[0].querySelector('.user-name')?.textContent.trim() || '';
                        const email = cells[1].textContent.trim();
                        const role = cells[2].textContent.trim();
                        const joined = cells[3].textContent.trim();
                        const status = row.getAttribute('data-status');
                        return `<tr>
                            <td>${name}</td>
                            <td>${email}</td>
                            <td>${role}</td>
                            <td>${joined}</td>
                            <td><span class="badge ${status}">${status.charAt(0).toUpperCase() + status.slice(1)}</span></td>
                        </tr>`;
                    }).join('')}
                </tbody>
            </table>
        </body>
        </html>
    `;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    printWindow.close();
}

console.log('Manage Users loaded - Type:', manageType);