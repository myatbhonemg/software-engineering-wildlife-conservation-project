// ===== STUDENT SUBMISSIONS JS =====

const STUDENT_ID = window.__STUDENT_ID__;

function showSection(name, btn) {
    document.querySelectorAll('.sub-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.sub-tab').forEach(b => b.classList.remove('active'));
    document.getElementById(`section-${name}`).classList.add('active');
    btn.classList.add('active');
}

document.addEventListener('DOMContentLoaded', function () {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab');
    if (tab) {
        const btn = document.querySelector(`.sub-tab[onclick*="'${tab}'"]`);
        if (btn) {
            document.querySelectorAll('.sub-tab').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.sub-section').forEach(s => s.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`section-${tab}`)?.classList.add('active');
        }
    }
});

// ===== GENERIC GRADING (programs, sightings, creative files) =====
// studentId is optional — falls back to STUDENT_ID (single-student page).
// On the class page each Save button passes the correct student's id explicitly.
async function saveGenericGrade(subjectType, subjectId, scoreElId, feedbackElId, cardId, studentId) {
    const targetStudent = studentId ?? STUDENT_ID;

    const scoreEl    = document.getElementById(scoreElId);
    const feedbackEl = document.getElementById(feedbackElId);
    const scoreVal   = scoreEl.value.trim();
    const feedback   = feedbackEl.value.trim();

    if (scoreVal !== '' && (isNaN(scoreVal) || +scoreVal < 0 || +scoreVal > 100)) {
        showToast('Score must be 0–100.', 'error');
        return;
    }

    const btn = scoreEl.closest('.grading-panel').querySelector('.btn-save-grade');
    btn.disabled    = true;
    btn.textContent = 'Saving…';

    try {
        const res  = await fetch(`/assess-student/${targetStudent}`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                subject_type: subjectType,
                subject_id:   subjectId,
                score:        scoreVal !== '' ? parseInt(scoreVal) : null,
                feedback:     feedback
            })
        });
        const data = await res.json();
        if (data.success) {
            const card  = document.getElementById(cardId);
            const badge = card.querySelector('.grade-badge');
            if (badge && scoreVal !== '') {
                badge.textContent = `${scoreVal}/100`;
                badge.classList.remove('ungraded');
                card.classList.add('graded');
            }
            const panel = scoreEl.closest('.grading-panel');
            let meta = panel.querySelector('.grade-meta');
            if (!meta) {
                meta = document.createElement('p');
                meta.className = 'grade-meta';
                panel.appendChild(meta);
            }
            const today = new Date().toISOString().slice(0, 10);
            meta.textContent = `Assessed by ${data.assessor_name} on ${today}`;
            showToast('Assessment saved ✓', 'success');
        } else {
            showToast(data.message || 'Failed to save.', 'error');
        }
    } catch {
        showToast('Network error.', 'error');
    } finally {
        btn.disabled    = false;
        btn.textContent = 'Save';
    }
}

function openFileViewer(fileUrl) {
    window.open(fileUrl, '_blank');
}

// ===== TOAST =====
function showToast(msg, type) {
    const toast = document.getElementById('grade-toast');
    if (!toast) return;
    toast.textContent   = msg;
    toast.className     = `grade-toast toast-${type}`;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}