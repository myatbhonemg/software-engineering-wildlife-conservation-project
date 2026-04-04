// ===== ACTIVITY JS =====

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

function signOut() {
    window.location.href = '/logout';
}

// ===== FILTER =====
function filterChallenges(filter, btn) {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    document.querySelectorAll('.challenge-card').forEach(card => {
        const status = card.getAttribute('data-status');
        const done = card.getAttribute('data-done') === '1';

        let show = false;
        if (filter === 'all') show = true;
        else if (filter === 'completed') show = done;
        else if (filter === 'active') show = status === 'active' && !done;
        else if (filter === 'expired') show = status === 'expired';

        card.style.display = show ? '' : 'none';
    });
}

// ===== CREATE CHALLENGE =====
function openCreateChallengeModal() {
    document.getElementById('create-challenge-modal').style.display = 'flex';
}

function closeCreateChallengeModal() {
    document.getElementById('create-challenge-modal').style.display = 'none';
    document.getElementById('challenge-title').value = '';
    document.getElementById('challenge-description').value = '';
    document.getElementById('challenge-points').value = '';
    document.getElementById('challenge-duration').value = '';
    document.getElementById('challenge-species').value = '';
}

function createChallenge() {
    const title       = document.getElementById('challenge-title').value.trim();
    const description = document.getElementById('challenge-description').value.trim();
    const points      = document.getElementById('challenge-points').value;
    const duration    = document.getElementById('challenge-duration').value;
    const species     = document.getElementById('challenge-species').value;

    if (!title || !description || !points || !duration) {
        alert('Please fill in all required fields.');
        return;
    }

    fetch('/create-challenge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            title, description,
            points: parseInt(points),
            duration_days: parseInt(duration),
            species_focus: species
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            closeCreateChallengeModal();
            location.reload();
        } else {
            alert(data.message || 'Failed to create challenge.');
        }
    });
}

// ===== SUBMIT EVIDENCE =====
let currentChallengeId = null;

function openSubmitModal(challengeId, title, points) {
    currentChallengeId = challengeId;
    document.getElementById('submit-modal-title').textContent = `Submit: ${title}`;
    document.getElementById('submit-modal-points').textContent = `🏆 You will earn ${points} points on submission`;
    document.getElementById('submit-modal').style.display = 'flex';
}

function closeSubmitModal() {
    document.getElementById('submit-modal').style.display = 'none';
    document.getElementById('evidence-input').value = '';
    document.getElementById('evidence-description').value = '';
    document.getElementById('evidence-preview').style.display = 'none';
    document.getElementById('evidence-img-preview').style.display = 'none';
    document.getElementById('evidence-vid-preview').style.display = 'none';
    currentChallengeId = null;
}

function previewEvidence(input) {
    const file = input.files[0];
    if (!file) return;

    const preview = document.getElementById('evidence-preview');
    const imgEl = document.getElementById('evidence-img-preview');
    const vidEl = document.getElementById('evidence-vid-preview');
    const nameEl = document.getElementById('evidence-filename');

    preview.style.display = 'block';
    nameEl.textContent = file.name;

    if (file.type.startsWith('image/')) {
        imgEl.src = URL.createObjectURL(file);
        imgEl.style.display = 'block';
        vidEl.style.display = 'none';
    } else if (file.type.startsWith('video/')) {
        vidEl.src = URL.createObjectURL(file);
        vidEl.style.display = 'block';
        imgEl.style.display = 'none';
    }
}

function submitEvidence() {
    const fileInput = document.getElementById('evidence-input');
    const description = document.getElementById('evidence-description').value.trim();

    if (!fileInput.files[0] && !description) {
        alert('Please upload a photo or video as evidence.');
        return;
    }

    const btn = document.getElementById('btn-submit-evidence');
    btn.textContent = 'Submitting...';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('description', description);
    if (fileInput.files[0]) formData.append('media', fileInput.files[0]);

    fetch(`/submit-challenge/${currentChallengeId}`, {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            closeSubmitModal();

            // Update card in DOM
            const card = document.getElementById(`challenge-card-${currentChallengeId}`);
            if (card) {
                card.setAttribute('data-done', '1');
                card.classList.add('done');
                const submitBtn = card.querySelector('.btn-submit');
                if (submitBtn) {
                    submitBtn.textContent = '✅ Completed';
                    submitBtn.className = 'btn-challenge btn-done';
                    submitBtn.disabled = true;
                }
                const badge = card.querySelector('.challenge-badge');
                if (badge) badge.innerHTML = '✅ Done';
                const pts = card.querySelector('.challenge-points');
                if (pts) pts.classList.add('earned');
            }

            // Show points toast
            showToast(`🏆 +${data.points_earned} points earned! Total: ${data.new_total} pts`);
        } else {
            alert(data.message || 'Submission failed.');
            btn.textContent = 'Submit & Earn Points';
            btn.disabled = false;
        }
    });
}

// ===== DELETE CHALLENGE =====
function deleteChallenge(challengeId) {
    if (!confirm('Delete this challenge? All submissions and awarded points will be removed.')) return;

    fetch(`/delete-challenge/${challengeId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const card = document.getElementById(`challenge-card-${challengeId}`);
            if (card) card.remove();
        } else {
            alert(data.message || 'Could not delete challenge.');
        }
    });
}

// ===== CHALLENGE CLASS ASSIGNMENT =====
let currentChallengeClassId = null;

function openChallengeClassModal(challengeId) {
    currentChallengeClassId = challengeId;
    document.getElementById('challenge-class-modal').style.display = 'flex';
    loadChallengeClasses(challengeId);
}

function closeChallengeClassModal() {
    document.getElementById('challenge-class-modal').style.display = 'none';
    currentChallengeClassId = null;
}

function loadChallengeClasses(challengeId) {
    const list = document.getElementById('challenge-class-list');
    list.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">Loading...</p>';

    // Fetch teacher's classes and already-assigned classes in parallel
    Promise.all([
        fetch('/my-classes').then(r => r.json()),
        fetch(`/get-challenge-classes/${challengeId}`).then(r => r.json())
    ])
    .then(([classesData, assignedData]) => {
        if (!classesData.classes.length) {
            list.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">You have no classes assigned yet.</p>';
            return;
        }

        const assignedIds = new Set(assignedData.class_ids);

        list.innerHTML = classesData.classes.map(c => `
            <label style="display:flex; align-items:center; gap:12px; padding:10px 12px;
                          background:var(--light-bg); border-radius:8px; cursor:pointer;">
                <input type="checkbox"
                       ${assignedIds.has(c.class_id) ? 'checked' : ''}
                       onchange="toggleChallengeClass(${challengeId}, ${c.class_id}, this.checked)"
                       style="width:16px; height:16px; accent-color:var(--secondary-green);">
                <span style="font-size:14px; font-weight:600; color:var(--text-dark);">
                    ${c.name}
                    ${c.subject
                        ? `<span style="font-size:12px; color:var(--text-muted); font-weight:400;"> — ${c.subject}</span>`
                        : ''}
                </span>
            </label>
        `).join('');
    });
}

function toggleChallengeClass(challengeId, classId, assign) {
    fetch('/toggle-challenge-class', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ challenge_id: challengeId, class_id: classId, assign })
    })
    .then(r => r.json())
    .then(data => {
        if (!data.success) alert(data.message || 'Failed to update.');
    });
}

// ===== TOAST NOTIFICATION =====
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'points-toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

function unsubmitChallenge(challengeId, btn) {
    if (!confirm('Withdraw your submission? This will remove your earned points.')) return;

    fetch(`/unsubmit-challenge/${challengeId}`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                // Swap button back to submit state
                btn.textContent = 'Submit Evidence';
                btn.className = 'btn-submit-challenge';
                btn.setAttribute('onclick', `openSubmitModal(${challengeId}, this)`);

                // Update points display if visible
                const pointsEl = document.getElementById('user-points');
                if (pointsEl) pointsEl.textContent = data.new_total;
            } else {
                alert(data.message || 'Could not withdraw submission.');
            }
        });
}

console.log('Activity loaded successfully');