// ===== CREATIVE CANVAS JS =====
// File: static/js/tabs/creative-canvas.js

function signOut() {
    window.location.href = '/logout';
}

// ── State ────────────────────────────────────────────────────────────────────
let pendingFile   = null;   // File object waiting for modal confirmation
let activeFilter  = 'all';

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setupDragDrop();
    document.getElementById('file-input').addEventListener('change', handleFileSelect);
});

// ── Drag & Drop ──────────────────────────────────────────────────────────────
function setupDragDrop() {
    const zone = document.getElementById('upload-zone');
    if (!zone) return;

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', (e) => {
        if (!zone.contains(e.relatedTarget)) {
            zone.classList.remove('dragover');
        }
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) validateAndQueue(files[0]);
    });
}

// ── File Selection ────────────────────────────────────────────────────────────
function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) validateAndQueue(files[0]);
    e.target.value = ''; // reset so same file can be re-selected
}

function validateAndQueue(file) {
    const MAX_SIZE    = 25 * 1024 * 1024; // 25 MB
    const ALLOWED_EXT = /\.(ppt|pptx|doc|docx|pdf|txt|xls|xlsx)$/i;

    if (!ALLOWED_EXT.test(file.name)) {
        showError(`"${file.name}" is not a supported format. Please upload PPT, PPTX, DOC, DOCX, PDF, XLS, XLSX, or TXT.`);
        return;
    }

    if (file.size > MAX_SIZE) {
        showError(`"${file.name}" exceeds the 25 MB limit (${(file.size / 1024 / 1024).toFixed(1)} MB).`);
        return;
    }

    // Queue and open modal for metadata
    pendingFile = file;
    openUploadModal(file.name);
}

// ── Upload Modal ──────────────────────────────────────────────────────────────
function openUploadModal(filename) {
    document.getElementById('modal-file-name').textContent = `📎 ${filename}`;
    document.getElementById('upload-title').value       = '';
    document.getElementById('upload-description').value = '';
    document.getElementById('upload-species').value     = '';
    document.getElementById('upload-modal').style.display = 'flex';
    setTimeout(() => document.getElementById('upload-title').focus(), 100);
}

function closeUploadModal() {
    document.getElementById('upload-modal').style.display = 'none';
    pendingFile = null;
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    const modal = document.getElementById('upload-modal');
    if (e.target === modal) closeUploadModal();
});

// ── Confirm Upload ────────────────────────────────────────────────────────────
async function confirmUpload() {
    const title = document.getElementById('upload-title').value.trim();
    if (!title) {
        document.getElementById('upload-title').classList.add('input-error');
        document.getElementById('upload-title').focus();
        return;
    }
    document.getElementById('upload-title').classList.remove('input-error');

    if (!pendingFile) return;

    const btn = document.getElementById('btn-upload-confirm');
    btn.disabled    = true;
    btn.textContent = 'Uploading…';

    const formData = new FormData();
    formData.append('file',        pendingFile);
    formData.append('title',       title);
    formData.append('description', document.getElementById('upload-description').value.trim());
    formData.append('species_tag', document.getElementById('upload-species').value);

    try {
        const res  = await fetch('/upload-creative-file', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.success) {
            closeUploadModal();
            showSuccess();
            // Reload page to show new file card
            setTimeout(() => window.location.reload(), 1200);
        } else {
            showError(data.message || 'Upload failed. Please try again.');
            btn.disabled    = false;
            btn.textContent = 'Upload File';
        }
    } catch (err) {
        showError('Network error. Please check your connection and try again.');
        btn.disabled    = false;
        btn.textContent = 'Upload File';
    }
}

// ── Delete File ───────────────────────────────────────────────────────────────
async function deleteFile(fileId, btn) {
    if (!confirm('Are you sure you want to delete this file?\n\nThis action cannot be undone.')) return;

    try {
        const res  = await fetch(`/delete-creative-file/${fileId}`, { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            // Remove card from DOM with animation
            const card = btn.closest('.file-card');
            card.style.transition = 'opacity 0.3s, transform 0.3s';
            card.style.opacity    = '0';
            card.style.transform  = 'scale(0.95)';
            setTimeout(() => {
                card.remove();
                updateStats();
                checkEmptyState();
            }, 300);
        } else {
            alert(data.message || 'Failed to delete file.');
        }
    } catch (err) {
        alert('Network error. Please try again.');
    }
}

// ── Filter Files ──────────────────────────────────────────────────────────────
function filterFiles(filter) {
    activeFilter = filter;

    // Update tab styles
    document.querySelectorAll('.canvas-tab').forEach(tab => {
        tab.classList.toggle('active', tab.getAttribute('data-filter') === filter);
    });

    const cards = document.querySelectorAll('.file-card');
    let visible = 0;

    cards.forEach(card => {
        const type  = card.getAttribute('data-type');
        const owner = card.getAttribute('data-owner');

        let show = false;
        if (filter === 'all')      show = true;
        else if (filter === 'my-files') show = owner === 'mine';
        else                            show = type === filter;

        card.style.display = show ? 'block' : 'none';
        if (show) visible++;
    });

    const grid          = document.getElementById('files-grid');
    const noFilter      = document.getElementById('no-filter-results');
    const noResults     = document.getElementById('no-results');

    if (grid) grid.style.display = visible > 0 ? 'grid' : 'none';
    if (noFilter) noFilter.style.display = (visible === 0 && cards.length > 0) ? 'block' : 'none';
    if (noResults) noResults.style.display = (cards.length === 0) ? 'block' : 'none';
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function showSuccess() {
    const el = document.getElementById('upload-success');
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 4000);
}

function showError(msg) {
    const el = document.getElementById('upload-error');
    el.textContent   = '❌ ' + msg;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}

function updateStats() {
    const allCards  = document.querySelectorAll('.file-card');
    const mineCards = document.querySelectorAll('.file-card[data-owner="mine"]');
    const total     = allCards.length;

    const statTotal = document.getElementById('stat-total');
    const statMine  = document.getElementById('stat-mine');
    if (statTotal) statTotal.textContent = `${total} file${total !== 1 ? 's' : ''}`;
    if (statMine)  statMine.textContent  = `${mineCards.length} uploaded by you`;
}

function checkEmptyState() {
    const cards     = document.querySelectorAll('.file-card');
    const noResults = document.getElementById('no-results');
    const grid      = document.getElementById('files-grid');
    if (cards.length === 0) {
        if (grid)      grid.style.display      = 'none';
        if (noResults) noResults.style.display = 'block';
    }
}

console.log('Creative Canvas v2 loaded');