// assess-submissions.js
// File: static/js/tabs/assess-submissions.js

function signOut() {
    window.location.href = '/logout';
}

async function saveGrade(submissionId) {
    const scoreEl    = document.getElementById(`score-${submissionId}`);
    const feedbackEl = document.getElementById(`feedback-${submissionId}`);
    const scoreVal   = scoreEl.value.trim();
    const feedback   = feedbackEl.value.trim();

    // Allow saving feedback without a score, but validate if score is given
    if (scoreVal !== '' && (isNaN(scoreVal) || +scoreVal < 0 || +scoreVal > 100)) {
        showToast('Score must be a number between 0 and 100.', 'error');
        scoreEl.focus();
        return;
    }

    const btn = scoreEl.closest('.grading-panel').querySelector('.btn-save-grade');
    btn.disabled    = true;
    btn.textContent = 'Saving…';

    try {
        const res  = await fetch(`/grade-submission/${submissionId}`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                score:    scoreVal !== '' ? parseInt(scoreVal) : null,
                feedback: feedback
            })
        });
        const data = await res.json();

        if (data.success) {
            // Update the grade badge on this card
            const card  = document.getElementById(`sub-card-${submissionId}`);
            const badge = card.querySelector('.grade-badge');
            if (scoreVal !== '') {
                badge.textContent = `${scoreVal}/100`;
                badge.classList.remove('ungraded');
                card.classList.add('graded');
            }
            showToast('Grade saved ✓', 'success');
            updateSummaryStats();
        } else {
            showToast(data.message || 'Failed to save grade.', 'error');
        }
    } catch (err) {
        showToast('Network error. Please try again.', 'error');
    } finally {
        btn.disabled    = false;
        btn.textContent = 'Save';
    }
}

function updateSummaryStats() {
    const badges  = document.querySelectorAll('.grade-badge:not(.ungraded)');
    const graded  = badges.length;
    const ungraded = document.querySelectorAll('.grade-badge.ungraded').length;
    const statEls = document.querySelectorAll('.assess-stat-n');
    if (statEls.length >= 3) {
        statEls[1].textContent = graded;
        statEls[2].textContent = ungraded;
    }
}

function showToast(msg, type) {
    const toast = document.getElementById('grade-toast');
    toast.textContent   = msg;
    toast.className     = `grade-toast toast-${type}`;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}