// ===== PROGRAMS JS =====

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

function signOut() {
    window.location.href = '/logout';
}

let currentProgramId = null;

function openProgramClassModal(programId) {
    currentProgramId = programId;
    document.getElementById('program-class-modal').style.display = 'flex';
    loadProgramClasses(programId);
}

function closeProgramClassModal() {
    document.getElementById('program-class-modal').style.display = 'none';
    currentProgramId = null;
}

function loadProgramClasses(programId) {
    const list = document.getElementById('program-class-list');
    list.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">Loading...</p>';

    fetch('/my-classes')
    .then(r => r.json())
    .then(data => {
        if (!data.classes.length) {
            list.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">You have no classes assigned yet.</p>';
            return;
        }

        // Also fetch which classes this program is already assigned to
        fetch(`/get-program-classes/${programId}`)
        .then(r => r.json())
        .then(assigned => {
            const assignedIds = new Set(assigned.class_ids);
            list.innerHTML = data.classes.map(c => `
                <label style="display:flex; align-items:center; gap:12px; padding:10px 12px;
                              background:var(--light-bg); border-radius:8px; cursor:pointer;">
                    <input type="checkbox"
                           ${assignedIds.has(c.class_id) ? 'checked' : ''}
                           onchange="toggleProgramClass(${programId}, ${c.class_id}, this.checked)"
                           style="width:16px; height:16px; accent-color:var(--secondary-green);">
                    <span style="font-size:14px; font-weight:600; color:var(--text-dark);">
                        ${c.name}
                        ${c.subject ? `<span style="font-size:12px; color:var(--text-muted); font-weight:400;"> — ${c.subject}</span>` : ''}
                    </span>
                </label>
            `).join('');
        });
    });
}

function toggleProgramClass(programId, classId, assign) {
    fetch('/toggle-program-class', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ program_id: programId, class_id: classId, assign })
    })
    .then(r => r.json())
    .then(data => {
        if (!data.success) alert(data.message || 'Failed to update.');
    });
}

// ===== MODALS =====
function openCreateProgramModal() {
    document.getElementById('create-program-modal').style.display = 'flex';
}

function closeCreateProgramModal() {
    document.getElementById('create-program-modal').style.display = 'none';
    document.getElementById('program-title').value = '';
    document.getElementById('program-description').value = '';
    document.getElementById('program-species').value = '';
    document.getElementById('program-duration').value = '';
    document.getElementById('program-files').value = '';
    selectedFiles = [];
    renderSelectedFiles();
}

// ===== FILE MANAGEMENT =====
let selectedFiles = []; // track files across multiple selections

function handleFileSelect(input) {
    const newFiles = Array.from(input.files);
    
    newFiles.forEach(file => {
        // Avoid duplicates by name
        if (!selectedFiles.find(f => f.name === file.name)) {
            selectedFiles.push(file);
        }
    });

    // Reset input so same file can be re-added after removal
    input.value = '';
    renderSelectedFiles();
}

// Rendering the selected files for program
function renderSelectedFiles() {
    const list = document.getElementById('selected-files-list');
    const dropZone = document.getElementById('file-drop-zone');

    if (selectedFiles.length === 0) {
        list.innerHTML = '';
        dropZone.classList.remove('has-files');
        return;
    }

    dropZone.classList.add('has-files');

    list.innerHTML = selectedFiles.map((file, index) => {
        const ext = file.name.split('.').pop().toUpperCase();
        const size = file.size < 1024 * 1024
            ? `${(file.size / 1024).toFixed(0)} KB`
            : `${(file.size / (1024 * 1024)).toFixed(1)} MB`;

        return `
            <div class="selected-file-item">
                <span class="file-ext-badge">${ext}</span>
                <span class="file-item-name">${file.name}</span>
                <span class="file-item-size">${size}</span>
                <button class="file-item-remove" onclick="removeFile(${index})" title="Remove">×</button>
            </div>`;
    }).join('');
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderSelectedFiles();
}

// ===== CREATE PROGRAM =====
function createProgram() {
    const title       = document.getElementById('program-title').value.trim();
    const description = document.getElementById('program-description').value.trim();
    const species     = document.getElementById('program-species').value;
    const duration    = document.getElementById('program-duration').value.trim();

    if (!title || !description) {
        alert('Please fill in the title and description.');
        return;
    }

    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('species_focus', species);
    formData.append('duration', duration);

    // Append all tracked files
    selectedFiles.forEach(file => formData.append('files', file));

    fetch('/create-program', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                closeCreateProgramModal();
                location.reload();
            } else {
                alert(data.message || 'Failed to create program.');
            }
        });
}


// ===== ENROLL =====
function enroll(programId, btn) {
    fetch(`/enroll/${programId}`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                btn.textContent = '✓ Enrolled — Unenroll';
                btn.className = 'btn-unenroll';
                btn.setAttribute('onclick', `unenroll(${programId}, this)`);

                // Update enrolled count
                const footer = btn.closest('.program-footer');
                const countEl = footer.querySelector('.enrolled-count');
                const current = parseInt(countEl.textContent.match(/\d+/)[0]);
                countEl.textContent = `👤 ${current + 1} enrolled`;
            } else {
                alert(data.message || 'Could not enroll.');
            }
        });
}

// ===== UNENROLL =====
function unenroll(programId, btn) {
    if (!confirm('Are you sure you want to unenroll from this program?')) return;

    fetch(`/unenroll/${programId}`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                btn.textContent = 'Enroll';
                btn.className = 'btn-enroll';
                btn.setAttribute('onclick', `enroll(${programId}, this)`);

                // Update enrolled count
                const footer = btn.closest('.program-footer');
                const countEl = footer.querySelector('.enrolled-count');
                const current = parseInt(countEl.textContent.match(/\d+/)[0]);
                countEl.textContent = `👤 ${Math.max(0, current - 1)} enrolled`;
            } else {
                alert(data.message || 'Could not unenroll.');
            }
        });
}

// ===== FILE PROGRESS for students=====
function completeFile(fileId, programId, btn) {
    fetch(`/complete-file/${fileId}`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (!data.success) { alert(data.message); return; }

            // Update button
            btn.textContent = '✓ Done';
            btn.classList.add('done');
            btn.setAttribute('onclick', `uncompleteFile(${fileId}, ${programId}, this)`);
            btn.setAttribute('title', 'Mark as incomplete');

            // Mark file row as done
            const fileItem = document.getElementById(`file-item-${fileId}`);
            if (fileItem) fileItem.classList.add('file-done');

            // Update progress bar
            updateProgressBar(programId, data.completed_count, data.total_count);

            // If program completed, replace unenroll button with completed badge
            if (data.program_completed) {
                const footer = document.querySelector(`#program-card-${programId} .program-footer`);
                const unenrollBtn = footer.querySelector('.btn-unenroll');
                if (unenrollBtn) {
                    unenrollBtn.outerHTML = `<span class="program-status-badge completed">✓ Completed</span>`;
                }
            }
        });
}

// Student can uncomplte the status of a file
function uncompleteFile(fileId, programId, btn) {
    fetch(`/uncomplete-file/${fileId}`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (!data.success) { alert(data.message); return; }

            // Update button
            btn.textContent = 'Mark Done';
            btn.classList.remove('done');
            btn.setAttribute('onclick', `completeFile(${fileId}, ${programId}, this)`);
            btn.setAttribute('title', 'Mark as complete');

            // Remove done state from file row
            const fileItem = document.getElementById(`file-item-${fileId}`);
            if (fileItem) fileItem.classList.remove('file-done');

            // Recalculate progress from DOM
            const card = document.getElementById(`program-card-${programId}`);
            const totalBtns = card.querySelectorAll('.btn-file-complete').length;
            const doneBtns = card.querySelectorAll('.btn-file-complete.done').length;
            updateProgressBar(programId, doneBtns, totalBtns);

            // Restore unenroll button if program was completed
            const footer = card.querySelector('.program-footer');
            const completedBadge = footer.querySelector('.program-status-badge.completed');
            if (completedBadge) {
                completedBadge.outerHTML = `
                    <button class="btn-unenroll"
                            onclick="unenroll(${programId}, this)">
                        ✓ Enrolled — Unenroll
                    </button>`;
            }
        });
}

// Handle updates in progress bar
function updateProgressBar(programId, done, total) {
    const progressEl = document.getElementById(`progress-${programId}`);
    if (!progressEl) return;
    const fill = progressEl.querySelector('.progress-bar-fill');
    const text = document.getElementById(`progress-text-${programId}`);
    const pct = total > 0 ? Math.round((done / total) * 100) : 0;
    fill.style.width = `${pct}%`;
    text.textContent = `${done} / ${total} complete`;
}

// ===== DELETE PROGRAM =====
function deleteProgram(programId) {
    if (!confirm('Delete this program? This will also remove all enrollments and files.')) return;

    fetch(`/delete-program/${programId}`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const card = document.getElementById(`program-card-${programId}`);
                if (card) card.remove();
            } else {
                alert(data.message || 'Could not delete program.');
            }
        });
}

console.log('Programs loaded successfully');