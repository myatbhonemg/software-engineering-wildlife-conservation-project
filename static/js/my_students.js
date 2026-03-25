/* my_students.js — Komodo Hub · Teacher: My Students */

(function () {
    "use strict";

    /* ── Search & Filter ─────────────────────────────────── */
    const searchInput     = document.getElementById("searchInput");
    const programmeFilter = document.getElementById("programmeFilter");
    const statusFilter    = document.getElementById("statusFilter");
    const rows            = document.querySelectorAll(".student-row");
    const noResults       = document.getElementById("noResults");

    function applyFilters() {
        const query  = searchInput ? searchInput.value.trim().toLowerCase() : "";
        const prog   = programmeFilter ? programmeFilter.value : "";
        const status = statusFilter ? statusFilter.value : "";
        let visible  = 0;

        rows.forEach(row => {
            const nameOk   = row.dataset.name.includes(query);
            const progOk   = !prog   || row.dataset.programme === prog;
            const statusOk = !status || row.dataset.status    === status;

            if (nameOk && progOk && statusOk) {
                row.classList.remove("hidden");
                visible++;
            } else {
                row.classList.add("hidden");
            }
        });

        if (noResults) {
            noResults.style.display = (visible === 0 && rows.length > 0) ? "block" : "none";
        }
    }

    searchInput     && searchInput.addEventListener("input", applyFilters);
    programmeFilter && programmeFilter.addEventListener("change", applyFilters);
    statusFilter    && statusFilter.addEventListener("change", applyFilters);

    const clearBtn = document.getElementById("clearFilters");
    clearBtn && clearBtn.addEventListener("click", () => {
        if (searchInput)     searchInput.value     = "";
        if (programmeFilter) programmeFilter.value = "";
        if (statusFilter)    statusFilter.value    = "";
        applyFilters();
    });

    /* ── Row Dropdown Menus ──────────────────────────────── */
    document.addEventListener("click", function (e) {
        const menuBtn = e.target.closest(".row-menu-btn");

        if (menuBtn) {
            e.stopPropagation();
            const wrap   = menuBtn.closest(".row-menu-wrap");
            const isOpen = wrap.classList.contains("open");

            // Close all open menus
            document.querySelectorAll(".row-menu-wrap.open")
                .forEach(w => w.classList.remove("open"));

            if (!isOpen) wrap.classList.add("open");

        } else if (!e.target.closest(".row-dropdown")) {
            document.querySelectorAll(".row-menu-wrap.open")
                .forEach(w => w.classList.remove("open"));
        }
    });

    /* ── Add Student Modal ───────────────────────────────── */
    const modal      = document.getElementById("addStudentModal");
    const openBtns   = [
        document.getElementById("addStudentBtn"),
        document.getElementById("emptyAddBtn")
    ];
    const closeBtns  = [
        document.getElementById("closeModal"),
        document.getElementById("cancelModal")
    ];

    function openModal()  {
        if (!modal) return;
        modal.style.display = "flex";
        document.body.style.overflow = "hidden";
    }

    function closeModal() {
        if (!modal) return;
        modal.style.display = "none";
        document.body.style.overflow = "";
    }

    openBtns.forEach(btn => btn && btn.addEventListener("click", openModal));
    closeBtns.forEach(btn => btn && btn.addEventListener("click", closeModal));

    modal && modal.addEventListener("click", function (e) {
        if (e.target === modal) closeModal();
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeModal();
    });

    /* ── Access Code Helpers ─────────────────────────────── */
    function makeCode() {
        const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        return Array.from({ length: 8 }, () =>
            chars[Math.floor(Math.random() * chars.length)]
        ).join("");
    }

    // Called by the Generate button inside the modal
    window.generateNewCode = function () {
        const input = document.getElementById("generatedCode");
        if (input) input.value = makeCode();
    };

    // Called by "Generate Access Code" in a row dropdown
    window.generateCode = function (studentId) {
        const code = makeCode();

        fetch("/teacher/students/" + studentId + "/generate-code", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken()
            },
            body: JSON.stringify({ code: code })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                navigator.clipboard.writeText(data.code).catch(function () {});
                showToast("Access code " + data.code + " copied to clipboard");
            }
        })
        .catch(function () {
            showToast("Could not generate code — please try again");
        });
    };

    /* ── Toast ───────────────────────────────────────────── */
    const toast    = document.getElementById("codeToast");
    const toastMsg = document.getElementById("toastMsg");
    let toastTimer;

    function showToast(msg) {
        if (!toast) return;
        toastMsg.textContent = msg;
        toast.classList.add("show");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            toast.classList.remove("show");
        }, 3200);
    }

    /* ── CSRF Helper ─────────────────────────────────────── */
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : "";
    }

    /* ── Animate progress bars on load ──────────────────── */
    document.querySelectorAll(".table-progress-fill").forEach(function (bar) {
        const target = bar.style.width;
        bar.style.width = "0";
        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                bar.style.width = target;
            });
        });
    });

}());
