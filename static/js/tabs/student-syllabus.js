// ============================================================
// student-syllabus.js
// Place at: static/js/tabs/student-syllabus.js
// ============================================================

// Sign out function
function signOut() {
    window.location.href = '/logout';
}

// ── Toggle topic collapse ────────────────────────────────────
function toggleTopic(btn) {
    const card = btn.closest('.topic-card');
    const list = card.querySelector('.activities-list');
    if (!list) return;
    const isHidden = list.style.display === 'none';
    list.style.display = isHidden ? 'block' : 'none';
    btn.textContent    = isHidden ? '⌄' : '⌃';
}

// ── Toggle activity complete ─────────────────────────────────
async function toggleActivityComplete(activityId, btn) {
    const res  = await fetch(`/syllabus/activity/${activityId}/toggle-complete`, { method: 'POST' });
    const data = await res.json();
    if (!data.success) { alert(data.message); return; }

    const row = document.getElementById(`act-row-${activityId}`);
    const titleEl = row.querySelector('.activity-title');

    if (data.completed) {
        btn.classList.add('checked');
        btn.innerHTML = '✓';
        row.classList.add('activity-done');
    } else {
        btn.classList.remove('checked');
        btn.innerHTML = '';
        row.classList.remove('activity-done');
    }

        refreshProgress();
    }

// ── Recalculate and update progress bar ──────────────────────
function refreshProgress() {
    // Count both manual (reading) and auto-completed (program/challenge/sighting) activities
    const allActivities  = document.querySelectorAll('.activity-check, .activity-check-placeholder');
    const doneActivities = document.querySelectorAll('.activity-check.checked, .activity-check-placeholder.checked');
    const total    = allActivities.length;
    const done     = doneActivities.length;
    const pct      = total > 0 ? Math.round(done / total * 100) : 0;

    const fill     = document.querySelector('.progress-fill');
    const pctLabel = document.querySelector('.progress-pct');
    const sub      = document.querySelector('.progress-sub');

    if (fill)     fill.style.width = pct + '%';
    if (pctLabel) pctLabel.textContent = pct + '%';
    if (sub)      sub.textContent = `${done} of ${total} activit${total !== 1 ? 'ies' : 'y'} completed`;

    // Update per-topic pip bars
    document.querySelectorAll('.topic-card').forEach(card => {
        const cardTotal = card.querySelectorAll('.activity-check, .activity-check-placeholder').length;
        const cardDone  = card.querySelectorAll('.activity-check.checked, .activity-check-placeholder.checked').length;
        const cardPct   = cardTotal > 0 ? Math.round(cardDone / cardTotal * 100) : 0;

        const pip   = card.querySelector('.topic-pip-fill');
        const count = card.querySelector('.activity-count');
        if (pip)   pip.style.width = cardPct + '%';
        if (count) count.textContent = `${cardDone}/${cardTotal} done`;
    });
}