// ============================================================
// syllabus.js  — UPDATED: adds drag-drop reorder + edit activity
// File: static/js/tabs/syllabus.js
// Replace your existing syllabus.js entirely with this file
// ============================================================

// ── Modal helpers ────────────────────────────────────────────
function closeModal(id) { document.getElementById(id).style.display = 'none'; }
function openModal(id)  { document.getElementById(id).style.display = 'flex'; }

document.addEventListener('click', e => {
    if (e.target.classList.contains('modal-overlay')) e.target.style.display = 'none';
});

function signOut() { window.location.href = '/logout'; }

// ── Toggle topic collapse ────────────────────────────────────
function toggleTopic(topicId) {
    const list = document.getElementById(`activities-${topicId}`);
    if (!list) return;
    list.style.display = list.style.display === 'none' ? 'block' : 'none';
}

// ── ITEM 5: Drag-and-drop reorder ────────────────────────────
// Uses the native HTML5 drag API — no external library needed
let dragSrcEl = null;

function setupDragDrop() {
    const list = document.getElementById('topics-list');
    if (!list) return;

    list.addEventListener('dragstart', e => {
        const card = e.target.closest('.topic-card');
        if (!card) return;
        dragSrcEl = card;
        card.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    });

    list.addEventListener('dragover', e => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        const card = e.target.closest('.topic-card');
        if (card && card !== dragSrcEl) {
            const rect   = card.getBoundingClientRect();
            const after  = e.clientY > rect.top + rect.height / 2;
            list.insertBefore(dragSrcEl, after ? card.nextSibling : card);
        }
    });

    list.addEventListener('dragend', async () => {
        if (!dragSrcEl) return;
        dragSrcEl.classList.remove('dragging');
        dragSrcEl = null;
        renumberTopics();

        // Persist new order
        const ids = [...list.querySelectorAll('.topic-card')]
                        .map(c => parseInt(c.dataset.topicId));
        await fetch(`/syllabus/${CLASS_ID}/reorder-topics`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ order: ids })
        });
    });

    // Make each card draggable via its handle
    list.querySelectorAll('.topic-drag-handle').forEach(handle => {
        handle.addEventListener('mousedown', () => {
            handle.closest('.topic-card').draggable = true;
        });
        handle.addEventListener('mouseup', () => {
            handle.closest('.topic-card').draggable = false;
        });
    });
}

document.addEventListener('DOMContentLoaded', setupDragDrop);

// ── Add topic ────────────────────────────────────────────────
function openAddTopicModal() {
    document.getElementById('topic-title').value     = '';
    document.getElementById('topic-objective').value = '';
    document.getElementById('topic-desc').value      = '';
    openModal('add-topic-modal');
    setTimeout(() => document.getElementById('topic-title').focus(), 100);
}

async function submitAddTopic() {
    const title     = document.getElementById('topic-title').value.trim();
    const objective = document.getElementById('topic-objective').value.trim();
    const desc      = document.getElementById('topic-desc').value.trim();
    if (!title) { alert('Topic title is required.'); return; }

    const res  = await fetch(`/syllabus/${CLASS_ID}/create-topic`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, learning_objective: objective, description: desc })
    });
    const data = await res.json();
    if (!data.success) { alert(data.message); return; }
    closeModal('add-topic-modal');
    appendTopicCard(data.topic);
    updateSummary();
    // Wire drag on new card
    setupDragDrop();
}

function appendTopicCard(topic) {
    const empty = document.querySelector('.syllabus-empty');
    if (empty) empty.remove();
    const list  = document.getElementById('topics-list');
    const count = list.querySelectorAll('.topic-card').length + 1;
    const card  = document.createElement('div');
    card.className        = 'topic-card';
    card.id               = `topic-card-${topic.topic_id}`;
    card.dataset.topicId  = topic.topic_id;
    card.innerHTML = `
        <div class="topic-header">
            <div class="topic-drag-handle" title="Drag to reorder">&#8801;</div>
            <div class="topic-number">${count}</div>
            <div class="topic-info">
                <h3 class="topic-title">${escHtml(topic.title)}</h3>
                ${topic.learning_objective ? `<p class="topic-objective">🎯 ${escHtml(topic.learning_objective)}</p>` : ''}
                ${topic.description        ? `<p class="topic-desc">${escHtml(topic.description)}</p>` : ''}
            </div>
            <div class="topic-meta">
                <span class="activity-count">0 activities</span>
            </div>
            <div class="topic-actions">
                <button class="btn-icon" onclick="openEditTopicModal(${topic.topic_id}, ${JSON.stringify(topic).replace(/"/g,'&quot;')})" title="Edit">&#9998;</button>
                <button class="btn-icon btn-icon-danger" onclick="deleteTopic(${topic.topic_id})" title="Delete">&#128465;</button>
                <button class="btn-icon btn-toggle-topic" onclick="toggleTopic(${topic.topic_id})" title="Expand">&#8964;</button>
            </div>
        </div>
        <div class="activities-list" id="activities-${topic.topic_id}">
            <div class="add-activity-row">
                <button class="btn-add-activity" onclick="openAddActivityModal(${topic.topic_id})">+ Add Activity</button>
            </div>
        </div>`;
    list.appendChild(card);
}

// ── Edit topic ───────────────────────────────────────────────
function openEditTopicModal(topicId, topic) {
    if (typeof topic === 'string') topic = JSON.parse(topic);
    document.getElementById('edit-topic-id').value        = topicId;
    document.getElementById('edit-topic-title').value     = topic.title || '';
    document.getElementById('edit-topic-objective').value = topic.learning_objective || '';
    document.getElementById('edit-topic-desc').value      = topic.description || '';
    openModal('edit-topic-modal');
}

async function submitEditTopic() {
    const id        = document.getElementById('edit-topic-id').value;
    const title     = document.getElementById('edit-topic-title').value.trim();
    const objective = document.getElementById('edit-topic-objective').value.trim();
    const desc      = document.getElementById('edit-topic-desc').value.trim();
    if (!title) { alert('Title is required.'); return; }

    const res  = await fetch(`/syllabus/topic/${id}/edit`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, learning_objective: objective, description: desc })
    });
    const data = await res.json();
    if (!data.success) { alert(data.message); return; }

    const card = document.getElementById(`topic-card-${id}`);
    if (card) {
        card.querySelector('.topic-title').textContent = title;
        const objEl = card.querySelector('.topic-objective');
        if (objective) {
            if (objEl) objEl.textContent = '🎯 ' + objective;
            else {
                const p = document.createElement('p');
                p.className = 'topic-objective';
                p.textContent = '🎯 ' + objective;
                card.querySelector('.topic-info').appendChild(p);
            }
        } else if (objEl) objEl.remove();
    }
    closeModal('edit-topic-modal');
}

// ── Delete topic ─────────────────────────────────────────────
async function deleteTopic(topicId) {
    if (!confirm('Delete this topic and all its activities?')) return;
    const res  = await fetch(`/syllabus/topic/${topicId}/delete`, { method: 'POST' });
    const data = await res.json();
    if (!data.success) { alert(data.message); return; }
    document.getElementById(`topic-card-${topicId}`)?.remove();
    renumberTopics();
    updateSummary();
}

// ── Add activity ─────────────────────────────────────────────
function openAddActivityModal(topicId) {
    document.getElementById('activity-topic-id').value = topicId;
    document.getElementById('activity-title').value    = '';
    document.getElementById('activity-desc').value     = '';
    document.getElementById('activity-type').value     = 'task';
    onActivityTypeChange();
    openModal('add-activity-modal');
    setTimeout(() => document.getElementById('activity-title').focus(), 100);
}

function onActivityTypeChange() {
    const type = document.getElementById('activity-type').value;
    document.getElementById('link-program-group').style.display   = type === 'program'   ? 'block' : 'none';
    document.getElementById('link-challenge-group').style.display = type === 'challenge' ? 'block' : 'none';
    document.getElementById('link-species-group').style.display   = type === 'sighting'  ? 'block' : 'none';
}



async function submitAddActivity() {
    const topicId     = document.getElementById('activity-topic-id').value;
    const title       = document.getElementById('activity-title').value.trim();
    const desc        = document.getElementById('activity-desc').value.trim();
    const type        = document.getElementById('activity-type').value;
    const programId   = type === 'program'   ? document.getElementById('activity-program').value   : null;
    const challengeId = type === 'challenge' ? document.getElementById('activity-challenge').value : null;
    const speciesId   = type === 'sighting'  ? document.getElementById('activity-species').value   : null; // ← moved here
    if (!title) { alert('Title is required.'); return; }

    const res = await fetch(`/syllabus/topic/${topicId}/create-activity`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description: desc, activity_type: type,
                               linked_program_id: programId || null,
                               linked_challenge_id: challengeId || null,
                               linked_species_id: speciesId || null })
    });
    const data = await res.json();
    if (!data.success) { alert(data.message); return; }
    closeModal('add-activity-modal');
    appendActivityRow(topicId, data.activity);
    updateActivityCount(topicId);
    updateSummary();
}

// ── ITEM 6: Edit activity ─────────────────────────────────────
// We inject an Edit button into each activity row. Call openEditActivityModal from HTML.
function openEditActivityModal(activityId, act) {
    if (typeof act === 'string') act = JSON.parse(act);

    // Reuse the add-activity modal fields — switch it to edit mode
    document.getElementById('activity-topic-id').value    = act.topic_id;
    document.getElementById('activity-title').value       = act.title || '';
    document.getElementById('activity-desc').value        = act.description || '';
    document.getElementById('activity-type').value        = act.activity_type || 'task';
    onActivityTypeChange();
    if (act.linked_program_id)   document.getElementById('activity-program').value   = act.linked_program_id;
    if (act.linked_challenge_id) document.getElementById('activity-challenge').value = act.linked_challenge_id;

    // Store editing id, change modal title and submit button
    document.getElementById('add-activity-modal').dataset.editId = activityId;
    document.querySelector('#add-activity-modal h2').textContent  = 'Edit Activity';

    // Swap submit handler
    const btn = document.querySelector('#add-activity-modal .btn-primary');
    btn.onclick    = () => submitEditActivity(activityId);
    btn.textContent = 'Save Changes';

    openModal('add-activity-modal');
    setTimeout(() => document.getElementById('activity-title').focus(), 100);
}

async function submitEditActivity(activityId) {
    const title       = document.getElementById('activity-title').value.trim();
    const desc        = document.getElementById('activity-desc').value.trim();
    const type        = document.getElementById('activity-type').value;
    const programId   = type === 'program'   ? document.getElementById('activity-program').value   : null;
    const challengeId = type === 'challenge' ? document.getElementById('activity-challenge').value : null;
    const speciesId   = type === 'sighting'  ? document.getElementById('activity-species').value   : null; // ← moved here
    if (!title) { alert('Title is required.'); return; }

    const res  = await fetch(`/syllabus/activity/${activityId}/edit`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description: desc, activity_type: type,
                               linked_program_id: programId || null,
                               linked_challenge_id: challengeId || null,
                            linked_species_id: speciesId || null })
    });
    const data = await res.json();
    if (!data.success) { alert(data.message); return; }

    // Update DOM row in place
    const row = document.getElementById(`activity-row-${activityId}`);
    if (row) {
        const act  = data.activity;
        const icon = TYPE_ICONS[act.activity_type] || '&#9989;';
        let linkHtml = '';
        if (act.program_title)   linkHtml = `<span class="activity-link">&#10132; Linked to program: ${escHtml(act.program_title)}</span>`;
        if (act.challenge_title) linkHtml = `<span class="activity-link">&#10132; Linked to challenge: ${escHtml(act.challenge_title)}</span>`;

        row.innerHTML = `
            <span class="activity-type-icon">${icon}</span>
            <div class="activity-info">
                <span class="activity-title">${escHtml(act.title)}</span>
                ${act.description ? `<span class="activity-desc">${escHtml(act.description)}</span>` : ''}
                ${linkHtml}
            </div>
            <span class="activity-type-badge type-${act.activity_type}">${cap(act.activity_type)}</span>
            <button class="btn-icon" onclick="openEditActivityModal(${act.activity_id}, ${JSON.stringify(act).replace(/"/g,'&quot;')})" title="Edit">&#9998;</button>
            <button class="btn-icon btn-icon-danger btn-sm"
                    onclick="deleteActivity(${act.activity_id}, ${act.topic_id})">&#128465;</button>`;
    }

    // Reset modal back to add mode
    resetActivityModal();
    closeModal('add-activity-modal');
}

function resetActivityModal() {
    const btn = document.querySelector('#add-activity-modal .btn-primary');
    btn.onclick     = submitAddActivity;
    btn.textContent = 'Add Activity';
    document.querySelector('#add-activity-modal h2').textContent = 'Add Activity';
    delete document.getElementById('add-activity-modal').dataset.editId;
}

// Patch the close handler to also reset
const origCloseModal = closeModal;
closeModal = function(id) {
    if (id === 'add-activity-modal') resetActivityModal();
    origCloseModal(id);
};

// ── Delete activity ──────────────────────────────────────────
async function deleteActivity(activityId, topicId) {
    if (!confirm('Delete this activity?')) return;
    const res  = await fetch(`/syllabus/activity/${activityId}/delete`, { method: 'POST' });
    const data = await res.json();
    if (!data.success) { alert(data.message); return; }
    document.getElementById(`activity-row-${activityId}`)?.remove();
    updateActivityCount(topicId);
    updateSummary();
}

// ── Helpers ──────────────────────────────────────────────────
const TYPE_ICONS = {
    program: '&#127942;', challenge: '&#9889;',
    sighting: '&#128248;', reading: '&#128214;', task: '&#9989;'
};

function appendActivityRow(topicId, act) {
    const list   = document.getElementById(`activities-${topicId}`);
    const addBtn = list.querySelector('.add-activity-row');
    const icon   = TYPE_ICONS[act.activity_type] || '&#9989;';
    let linkHtml = '';
    if (act.program_title)   linkHtml = `<span class="activity-link">&#10132; Linked to program: ${escHtml(act.program_title)}</span>`;
    if (act.challenge_title) linkHtml = `<span class="activity-link">&#10132; Linked to challenge: ${escHtml(act.challenge_title)}</span>`;

    const row = document.createElement('div');
    row.className = 'activity-row';
    row.id        = `activity-row-${act.activity_id}`;
    row.innerHTML = `
        <span class="activity-type-icon">${icon}</span>
        <div class="activity-info">
            <span class="activity-title">${escHtml(act.title)}</span>
            ${act.description ? `<span class="activity-desc">${escHtml(act.description)}</span>` : ''}
            ${linkHtml}
        </div>
        <span class="activity-type-badge type-${act.activity_type}">${cap(act.activity_type)}</span>
        <button class="btn-icon" onclick="openEditActivityModal(${act.activity_id}, ${JSON.stringify(act).replace(/"/g,'&quot;')})" title="Edit">&#9998;</button>
        <button class="btn-icon btn-icon-danger btn-sm"
                onclick="deleteActivity(${act.activity_id}, ${topicId})">&#128465;</button>`;
    list.insertBefore(row, addBtn);
}

function updateActivityCount(topicId) {
    const card  = document.getElementById(`topic-card-${topicId}`);
    if (!card) return;
    const count   = card.querySelectorAll('.activity-row').length;
    const counter = card.querySelector('.activity-count');
    if (counter) counter.textContent = `${count} activit${count !== 1 ? 'ies' : 'y'}`;
}

function updateSummary() {
    const topicCount = document.querySelectorAll('.topic-card').length;
    const actCount   = document.querySelectorAll('.activity-row').length;
    const strip      = document.querySelector('.syllabus-summary');
    if (strip) {
        strip.innerHTML = `
            <span class="summary-label">${topicCount} topic${topicCount !== 1 ? 's' : ''}</span>
            <span class="summary-sep">·</span>
            <span class="summary-label">${actCount} activit${actCount !== 1 ? 'ies' : 'y'}</span>`;
    }
}

function renumberTopics() {
    document.querySelectorAll('.topic-card .topic-number').forEach((el, i) => {
        el.textContent = i + 1;
    });
}

function escHtml(str) {
    return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;')
                             .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function cap(str) { return str ? str.charAt(0).toUpperCase() + str.slice(1) : ''; }