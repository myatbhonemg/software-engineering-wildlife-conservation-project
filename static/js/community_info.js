/* community_info.js — Komodo Hub · My Community tab */

(function () {
    "use strict";

    /* ── Edit / Cancel Details ───────────────────────────── */
    const editDetailsBtn  = document.getElementById("editDetailsBtn");
    const cancelDetailsBtn = document.getElementById("cancelDetailsBtn");
    const detailsView     = document.getElementById("detailsView");
    const detailsEdit     = document.getElementById("detailsEdit");

    editDetailsBtn && editDetailsBtn.addEventListener("click", function () {
        detailsView.style.display = "none";
        detailsEdit.style.display = "grid";
        editDetailsBtn.style.display = "none";
    });

    cancelDetailsBtn && cancelDetailsBtn.addEventListener("click", function () {
        detailsEdit.style.display = "none";
        detailsView.style.display = "grid";
        editDetailsBtn.style.display = "inline-block";
    });

    /* ── Avatar Modal ────────────────────────────────────── */
    const avatarModal      = document.getElementById("avatarModal");
    const changeAvatarBtn  = document.getElementById("changeAvatarBtn");
    const closeAvatarModal = document.getElementById("closeAvatarModal");
    const cancelAvatarModal = document.getElementById("cancelAvatarModal");
    const saveAvatarBtn    = document.getElementById("saveAvatarBtn");
    const avatarDisplay    = document.querySelector(".profile-avatar-large");

    let selectedAvatar = null;

    changeAvatarBtn && changeAvatarBtn.addEventListener("click", function () {
        avatarModal.style.display = "flex";
        document.body.style.overflow = "hidden";
    });

    function closeAvatar() {
        avatarModal.style.display = "none";
        document.body.style.overflow = "";
        selectedAvatar = null;
        document.querySelectorAll(".avatar-option").forEach(function (opt) {
            opt.classList.remove("selected");
        });
    }

    closeAvatarModal  && closeAvatarModal.addEventListener("click", closeAvatar);
    cancelAvatarModal && cancelAvatarModal.addEventListener("click", closeAvatar);

    avatarModal && avatarModal.addEventListener("click", function (e) {
        if (e.target === avatarModal) closeAvatar();
    });

    saveAvatarBtn && saveAvatarBtn.addEventListener("click", function () {
        if (!selectedAvatar) {
            closeAvatar();
            return;
        }
        if (avatarDisplay) avatarDisplay.textContent = selectedAvatar;
        showToast("Community icon updated");
        closeAvatar();
    });

    /* ── Avatar Selection ────────────────────────────────── */
    window.selectAvatar = function (emoji) {
        selectedAvatar = emoji;
        document.querySelectorAll(".avatar-option").forEach(function (opt) {
            opt.classList.remove("selected");
        });
        event.currentTarget.classList.add("selected");
    };

    /* ── Form Submit (AJAX) ──────────────────────────────── */
    const detailsForm = document.getElementById("detailsEdit");

    detailsForm && detailsForm.addEventListener("submit", function (e) {
        e.preventDefault();

        const formData = new FormData(detailsForm);
        const data = Object.fromEntries(formData.entries());

        fetch(detailsForm.action, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken()
            },
            body: JSON.stringify(data)
        })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                // Update the view fields with the new values
                updateViewField("Organisation Name", data.name);
                updateViewField("Type", data.type || "Not specified");
                updateViewField("Email Address", data.email);
                updateViewField("Address", data.address || "Not provided");

                // Update header name too
                const headerName = document.querySelector(".profile-header-info h2");
                if (headerName) headerName.textContent = data.name;

                // Update email in header
                const headerEmail = document.querySelector(".profile-email-text");
                if (headerEmail) headerEmail.textContent = data.email;

                // Switch back to view mode
                detailsEdit.style.display = "none";
                detailsView.style.display = "grid";
                editDetailsBtn.style.display = "inline-block";

                showToast("Community details saved");
            } else {
                showToast(res.message || "Could not save — please try again");
            }
        })
        .catch(function () {
            showToast("Could not save — please try again");
        });
    });

    function updateViewField(labelText, value) {
        const labels = document.querySelectorAll("#detailsView .info-item label");
        labels.forEach(function (label) {
            if (label.textContent.trim() === labelText) {
                const p = label.nextElementSibling;
                if (p) p.textContent = value;
            }
        });
    }

    /* ── Escape key closes modals ────────────────────────── */
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeAvatar();
    });

    /* ── Toast ───────────────────────────────────────────── */
    let toastEl = document.getElementById("communityToast");

    if (!toastEl) {
        toastEl = document.createElement("div");
        toastEl.id = "communityToast";
        toastEl.className = "community-toast";
        toastEl.innerHTML = '<span id="communityToastMsg"></span>';
        document.body.appendChild(toastEl);
    }

    let toastTimer;

    function showToast(msg) {
        const msgEl = document.getElementById("communityToastMsg");
        if (msgEl) msgEl.textContent = msg;
        toastEl.classList.add("show");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            toastEl.classList.remove("show");
        }, 3000);
    }

    /* ── CSRF Helper ─────────────────────────────────────── */
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : "";
    }

}());
