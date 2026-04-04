// notes.js
// File: static/js/tabs/notes.js

let _noteType      = 'announcement';
let _noteStudentId = null;

function openNoteModal(type, studentId) {
    _noteType      = type;
    _noteStudentId = studentId;

    const isPrivate = type === 'private';
    document.getElementById('note-modal-title').textContent =
        isPrivate ? '🔒 Private Note' : '📢 New Announcement';
    document.getElementById('note-label').textContent =
        isPrivate ? 'Note (visible only to this student\'s teacher)' : 'Announcement (visible to all class)';
    document.getElementById('note-body').value = '';
    document.getElementById('note-type-val').value  = type;
    document.getElementById('note-student-id').value = studentId || '';

    document.getElementById('note-modal').style.display = 'flex';
    setTimeout(() => document.getElementById('note-body').focus(), 80);
}

function closeNoteModal() {
    document.getElementById('note-modal').style.display = 'none';
}

// Close on overlay click
document.addEventListener('click', e => {
    if (e.target.id === 'note-modal') closeNoteModal();
});

async function submitNote() {
    const body = document.getElementById('note-body').value.trim();
    if (!body) {
        document.getElementById('note-body').classList.add('input-error');
        return;
    }
    document.getElementById('note-body').classList.remove('input-error');

    const btn       = document.querySelector('#note-modal .btn-confirm');
    btn.disabled    = true;
    btn.textContent = 'Posting…';

    try {
        const res  = await fetch(`/notes/${CLASS_ID}/create`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                body:              body,
                note_type:         _noteType,
                target_student_id: _noteStudentId || null
            })
        });
        const data = await res.json();

        if (data.success) {
            closeNoteModal();
            appendNoteCard(data.note, _noteType, _noteStudentId);
        } else {
            alert(data.message || 'Failed to post note.');
        }
    } catch (err) {
        alert('Network error.');
    } finally {
        btn.disabled    = false;
        btn.textContent = 'Post Note';
    }
}

function appendNoteCard(note, type, studentId) {
    const cardHtml = `
        <div class="note-card ${type === 'private' ? 'private' : ''}" id="note-${note.note_id}">
            <div class="note-body">${escHtml(note.body)}</div>
            <div class="note-footer">
                <span>Just now</span>
                <button class="btn-del-note" onclick="deleteNote(${note.note_id})">🗑</button>
            </div>
        </div>`;

    if (type === 'announcement') {
        const list  = document.getElementById('announcements-list');
        const empty = document.getElementById('ann-empty');
        if (empty) empty.remove();
        list.insertAdjacentHTML('afterbegin', cardHtml);
    } else {
        // Private note — find the student's notes container
        const snr = document.getElementById(`snr-notes-${studentId}`);
        if (snr) {
            const emptyMsg = snr.querySelector('.snr-empty');
            if (emptyMsg) emptyMsg.remove();
            snr.insertAdjacentHTML('afterbegin', cardHtml);
            snr.style.display = 'block'; // expand
            // Update badge count
            const row   = snr.closest('.student-note-row');
            let   badge = row.querySelector('.snr-badge');
            if (!badge) {
                const nameEl = row.querySelector('.snr-name');
                badge = document.createElement('span');
                badge.className = 'snr-badge';
                nameEl.insertAdjacentElement('afterend', badge);
            }
            badge.textContent = (parseInt(badge.textContent) || 0) + 1;
        }
    }
}

async function deleteNote(noteId) {
    if (!confirm('Delete this note?')) return;
    const res  = await fetch(`/notes/delete/${noteId}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
        document.getElementById(`note-${noteId}`)?.remove();
    } else {
        alert(data.message || 'Failed to delete note.');
    }
}

function toggleStudentNotes(studentId) {
    const el = document.getElementById(`snr-notes-${studentId}`);
    if (!el) return;
    const isOpen = el.style.display !== 'none';
    el.style.display = isOpen ? 'none' : 'block';
    // Flip chevron
    const row    = el.closest('.student-note-row');
    const chev   = row?.querySelector('.snr-chevron');
    if (chev) chev.textContent = isOpen ? '▾' : '▴';
}

function escHtml(str) {
    return String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}