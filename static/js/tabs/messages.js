// ===== MESSAGES JS =====
let pendingAttachment = null;

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

function signOut() {
    window.location.href = '/logout';
}

// ===== SEARCH USERS =====
function searchUsers(query) {
    const resultsDiv = document.getElementById('user-search-results');
    if (!query.trim()) {
        resultsDiv.innerHTML = '';
        return;
    }

    fetch(`/search-users?q=${encodeURIComponent(query)}`)
        .then(r => r.json())
        .then(data => {
            resultsDiv.innerHTML = '';
            if (data.users.length === 0) {
                resultsDiv.innerHTML = `<p style="padding:8px; color:var(--text-muted); font-size:13px;">No users found</p>`;
                return;
            }
            data.users.forEach(u => {
                const div = document.createElement('div');
                div.style.cssText = 'padding:10px; cursor:pointer; border-radius:6px; display:flex; align-items:center; gap:10px;';
                div.onmouseover = () => div.style.background = 'var(--light-bg)';
                div.onmouseout = () => div.style.background = '';
                div.innerHTML = `
                    <div style="width:32px;height:32px;border-radius:50%;background:var(--secondary-green);
                                display:flex;align-items:center;justify-content:center;overflow:hidden;">
                        ${u.avatar
                            ? `<img src="/static/${u.avatar}" style="width:100%;height:100%;object-fit:cover;">`
                            : '👤'}
                    </div>
                    <div>
                        <div style="font-weight:600; font-size:14px;">${u.fullname}</div>
                        <div style="font-size:12px; color:var(--text-muted);">${u.role.replace(/-/g, ' ')}</div>
                    </div>`;
                div.onclick = () => startChatWith(u);
                resultsDiv.appendChild(div);
            });
        });
}

// ===== OPEN CONVERSATION =====
function openConversation(userId, name, role, avatar) {
    // Update active state
    document.querySelectorAll('.conversation-item').forEach(i => i.classList.remove('active'));
    const item = document.querySelector(`.conversation-item[data-user-id="${userId}"]`);
    if (item) {
        item.classList.add('active');
        item.classList.remove('unread');
        const badge = item.querySelector('.unread-badge');
        if (badge) badge.remove();
    }

    // Update thread header
    const avatarEl = document.querySelector('.thread-avatar');
    avatarEl.innerHTML = avatar
        ? `<img src="/static/${avatar}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`
        : '👤';
    document.querySelector('.thread-info h3').textContent = name;
    document.querySelector('.thread-info p').textContent = role.replace(/-/g, ' ');

    // Store receiver
    document.getElementById('current-receiver-id').value = userId;

    // Fetch messages
    fetch(`/get-messages/${userId}`)
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;

            const myId = parseInt(document.getElementById('current-user-id').value);
            const thread = document.getElementById('messages-thread');
            thread.innerHTML = '';

            if (data.messages.length === 0) {
                thread.innerHTML = `<div data-placeholder style="text-align:center; padding:40px; color:var(--text-muted);">
                    No messages yet. Say hello!
                </div>`;
                return;
            }

            data.messages.forEach(msg => {
                const isSent = msg.sender_id === myId;
                const div = document.createElement('div');
                div.className = `message ${isSent ? 'sent' : 'received'}`;

                const isImage = msg.attachment && /\.(png|jpg|jpeg|gif|webp)$/i.test(msg.attachment);
                const attachmentHtml = msg.attachment
                    ? (isImage
                        ? `<img src="/static/${msg.attachment}" class="msg-attachment-img"
                                onclick="window.open(this.src,'_blank')">`
                        : `<a href="/static/${msg.attachment}" target="_blank"
                            class="msg-attachment-file">&#128206; Attachment</a>`)
                    : '';

                if (isSent) {
                    div.innerHTML = `
                        <div class="message-content">
                            <div class="message-header">
                                <span class="message-time">${formatTime(msg.sent_at)}</span>
                            </div>
                            ${msg.body ? `<p class="message-text">${escapeHtml(msg.body)}</p>` : ''}
                            ${attachmentHtml}
                        </div>`;
                } else {
                    div.innerHTML = `
                        <div class="message-avatar">
                            ${avatar ? `<img src="/static/${avatar}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">` : '👤'}
                        </div>
                        <div class="message-content">
                            <div class="message-header">
                                <span class="message-sender">${msg.sender_name}</span>
                                <span class="message-time">${formatTime(msg.sent_at)}</span>
                            </div>
                            ${msg.body ? `<p class="message-text">${escapeHtml(msg.body)}</p>` : ''}
                            ${attachmentHtml}
                        </div>`;
                }
                thread.appendChild(div);
            });
            thread.scrollTop = thread.scrollHeight;
        });
}

function startChatWith(u) {
    closeNewMessageModal();

    // If conversation already exists just open it
    const existing = document.querySelector(`.conversation-item[data-user-id="${u.user_id}"]`);
    if (existing) {
        openConversation(u.user_id, u.fullname, u.role, u.avatar || '');
        return;
    }

    // Add new entry to sidebar
    // ← Add this: remove the "No conversations yet" placeholder if present
    const convList = document.getElementById('conversations-list');
    const placeholder = convList.querySelector('[data-placeholder]');
    if (placeholder) placeholder.remove();

    const div = document.createElement('div');
    div.className = 'conversation-item active';
    div.setAttribute('data-user-id', u.user_id);
    div.onclick = () => openConversation(u.user_id, u.fullname, u.role, u.avatar || '');
    div.innerHTML = `
        <div class="conv-avatar">
            ${u.avatar
                ? `<img src="/static/${u.avatar}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`
                : '👤'}
        </div>
        <div class="conv-info">
            <div class="conv-header">
                <span class="conv-name">${u.fullname}</span>
                <span class="conv-time">New</span>
            </div>
            <p class="conv-preview">Start a conversation...</p>
        </div>`;
    document.querySelectorAll('.conversation-item').forEach(i => i.classList.remove('active'));
    convList.insertBefore(div, convList.firstChild);

    openConversation(u.user_id, u.fullname, u.role, u.avatar || '');
}

//====== HANDLE ATTACHMENTS
function handleAttachment(input) {
    const file = input.files[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
        alert('File too large. Max 10MB.');
        input.value = '';
        return;
    }
    pendingAttachment = file;
    document.getElementById('attachment-name').textContent = file.name;
    document.getElementById('attachment-preview').style.display = 'flex';
}

// ===== CLEAR ATTACHMENTS
function clearAttachment() {
    pendingAttachment = null;
    document.getElementById('attachment-input').value = '';
    document.getElementById('attachment-preview').style.display = 'none';
}

// ===== SEND MESSAGE =====
function sendMessage() {
    const input      = document.getElementById('message-input');
    const body       = input.value.trim();
    const receiverId = document.getElementById('current-receiver-id').value;

    if (!body && !pendingAttachment) return;
    if (!receiverId) { alert('Please select a conversation first'); return; }

    // Use FormData instead of JSON to support file upload
    const formData = new FormData();
    formData.append('body', body);
    formData.append('receiver_id', receiverId);
    if (pendingAttachment) formData.append('attachment', pendingAttachment);

    fetch('/send-message', { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
        if (!data.success) return;

        const thread = document.getElementById('messages-thread');
        const placeholder = thread.querySelector('[data-placeholder]');
        if (placeholder) placeholder.remove();

        // Build message bubble
        let attachmentHtml = '';
        if (data.attachment) {
            const isImage = /\.(png|jpg|jpeg|gif|webp)$/i.test(data.attachment);
            attachmentHtml = isImage
                ? `<img src="/static/${data.attachment}" class="msg-attachment-img"
                        onclick="window.open(this.src,'_blank')">`
                : `<a href="/static/${data.attachment}" target="_blank"
                      class="msg-attachment-file">&#128206; ${pendingAttachment?.name || 'Attachment'}</a>`;
        }

        const div = document.createElement('div');
        div.className = 'message sent';
        div.innerHTML = `
            <div class="message-content">
                <div class="message-header">
                    <span class="message-time">${formatTime(data.sent_at)}</span>
                </div>
                ${body ? `<p class="message-text">${escapeHtml(body)}</p>` : ''}
                ${attachmentHtml}
            </div>`;
        thread.appendChild(div);
        thread.scrollTop = thread.scrollHeight;

        // Update sidebar preview
        const item = document.querySelector(`.conversation-item[data-user-id="${receiverId}"]`);
        if (item) {
            item.querySelector('.conv-preview').textContent = body || '📎 Attachment';
            item.querySelector('.conv-time').textContent = 'Just now';
        }

        input.value = '';
        clearAttachment();
    });
}

// ===== MODAL =====
function newMessage() {
    document.getElementById('new-message-modal').style.display = 'flex';
    setTimeout(() => document.getElementById('new-message-username').focus(), 100);
}

function closeNewMessageModal() {
    document.getElementById('new-message-modal').style.display = 'none';
    document.getElementById('new-message-username').value = '';
    document.getElementById('user-search-results').innerHTML = '';
}

// ===== HELPERS =====
function formatTime(datetimeStr) {
    if (!datetimeStr) return '';
    const date = new Date(datetimeStr);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const isYesterday = new Date(now - 86400000).toDateString() === date.toDateString();
    const timeStr = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    if (isToday) return `Today, ${timeStr}`;
    if (isYesterday) return `Yesterday, ${timeStr}`;
    return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// Enter to send (Shift+Enter for new line)
document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('message-input');
    if (input) {
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    // Enter in search modal
    const searchInput = document.getElementById('new-message-username');
    if (searchInput) {
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeNewMessageModal();
        });
    }
        // Auto-open conversation if ?open=userId is in URL
    const params = new URLSearchParams(window.location.search);
    const openUserId = params.get('open');
    if (openUserId) {
        const item = document.querySelector(`.conversation-item[data-user-id="${openUserId}"]`);
        if (item) {
            // Conversation already exists, just open it
            item.click();
        } else {
            // Fetch user info and start new conversation
            fetch(`/search-users?q=id:${openUserId}`)
                .then(r => r.json())
                .then(data => {
                    if (data.users && data.users.length > 0) {
                        startChatWith(data.users[0]);
                    }
                });
        }
    }

});

console.log('Messages loaded successfully');