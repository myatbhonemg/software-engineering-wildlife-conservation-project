// ===== MESSAGES JS =====

// Check user authentication
const user = JSON.parse(localStorage.getItem('user'));

if (!user) {
    window.location.href = '../login.html';
}

// Update UI with user info
if (user) {
    const navUsername = document.getElementById('nav-username');
    if (navUsername) navUsername.textContent = user.name;

    const roleBadge = document.getElementById('user-role-badge');
    if (roleBadge) {
        const roleNames = {
            'student': 'Student',
            'teacher': 'Teacher',
            'principal': 'Principal',
            'school-admin': 'School Admin',
            'community-member': 'Community',
            'community-admin': 'Community Admin',
            'system-admin': 'System Admin',
            'public': 'Guest'
        };
        roleBadge.textContent = roleNames[user.role] || user.role;
    }
}

// Sign out function
function signOut() {
    localStorage.removeItem('user');
    window.location.href = '/logout';
}

// Toggle sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

// ===== MESSAGES FUNCTIONALITY =====

// Open conversation
function openConversation(conversationId) {
    // Remove active from all conversations
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active to clicked conversation (use event.currentTarget)
    const clickedItem = event.currentTarget;
    clickedItem.classList.add('active');
    
    // Remove unread badge and unread class
    clickedItem.classList.remove('unread');
    const badge = clickedItem.querySelector('.unread-badge');
    if (badge) badge.remove();
    
    // Mock conversation data
    const conversations = {
        1: {
            name: 'Sir Myat',
            role: 'Teacher, Biology',
            avatar: '🐅',
            messages: [
                { type: 'received', sender: 'Sir Myat', time: 'Yesterday, 2:30 PM', text: 'Hi! I reviewed your sighting report from last week. The observations were very detailed and accurate.' },
                { type: 'sent', time: 'Yesterday, 3:15 PM', text: 'Thank you, Mr. Johnson! I tried to capture as many details as possible. The rhino was about 50 meters away from our observation point.' },
                { type: 'received', sender: 'Sir Myat', time: 'Today, 10:30 AM', text: 'Great work on your sighting report! The photo quality is excellent. Would you be interested in presenting this at our next conservation club meeting?' },
                { type: 'received', sender: 'Sir Myat', time: 'Today, 10:32 AM', text: 'I think your classmates would love to hear about your experience!' }
            ]
        },
        2: {
            name: 'Kifo',
            role: 'Student, Grade 10',
            avatar: '🐒',
            messages: [
                { type: 'received', sender: 'Kifo', time: 'Yesterday, 4:20 PM', text: 'Hey! Did you see the Komodo Dragon at the national park yesterday?' },
                { type: 'sent', time: 'Yesterday, 5:10 PM', text: 'Yes! It was incredible. I managed to get some photos from a safe distance.' },
                { type: 'received', sender: 'Kifo', time: 'Yesterday, 5:15 PM', text: 'That\'s amazing! Can you share them with the conservation club?' }
            ]
        },
        3: {
            name: 'Conservation Team',
            role: 'School Program',
            avatar: '🐘',
            messages: [
                { type: 'received', sender: 'Conservation Team', time: '2 days ago', text: 'Reminder: Field trip to Ujung Kulon National Park next week. Please bring your camera and notebook.' },
                { type: 'received', sender: 'Conservation Team', time: '2 days ago', text: 'We\'ll be observing Javan Rhinos in their natural habitat. This is a rare opportunity!' }
            ]
        },
        4: {
            name: 'Odala',
            role: 'Student, Grade 11',
            avatar: '🦜',
            messages: [
                { type: 'received', sender: 'Odala', time: 'Feb 18, 3:00 PM', text: 'Hey, I saw your post about the Bali Myna. Do you have more info about their habitat?' },
                { type: 'sent', time: 'Feb 18, 4:30 PM', text: 'Sure! They mostly live in the Bali Barat National Park. I can send you the species library link.' },
                { type: 'received', sender: 'Odala', time: 'Feb 18, 5:00 PM', text: 'Thanks for sharing the species info! Really helpful for my project.' }
            ]
        },
        5: {
            name: 'Mr. Tevin',
            role: 'Teacher, Environmental Science',
            avatar: '🦧',
            messages: [
                { type: 'received', sender: 'Mr. Tevin', time: 'Feb 15, 10:00 AM', text: 'Your project proposal looks excellent. Let\'s discuss the timeline for your research.' },
                { type: 'sent', time: 'Feb 15, 2:30 PM', text: 'Thank you! I was thinking of starting observations next month. Would that work?' },
                { type: 'received', sender: 'Mr. Tevin', time: 'Feb 15, 3:00 PM', text: 'Perfect timing! I\'ll book the equipment for you.' }
            ]
        }
    };
    
    const conv = conversations[conversationId];
    if (!conv) return;
    
    // Update thread header
    document.querySelector('.thread-avatar').textContent = conv.avatar;
    document.querySelector('.thread-info h3').textContent = conv.name;
    document.querySelector('.thread-info p').textContent = conv.role;
    
    // Update messages thread
    const messagesThread = document.getElementById('messages-thread');
    messagesThread.innerHTML = '';
    
    conv.messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.type}`;
        
        if (msg.type === 'received') {
            messageDiv.innerHTML = `
                <div class="message-avatar">${conv.avatar}</div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-sender">${msg.sender}</span>
                        <span class="message-time">${msg.time}</span>
                    </div>
                    <p class="message-text">${msg.text}</p>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-time">${msg.time}</span>
                    </div>
                    <p class="message-text">${msg.text}</p>
                </div>
            `;
        }
        
        messagesThread.appendChild(messageDiv);
    });
    
    // Scroll to bottom
    messagesThread.scrollTop = messagesThread.scrollHeight;
    
    console.log('Opened conversation:', conversationId);
}

// Send message
function sendMessage() {
    const input = document.getElementById('message-input');
    const messageText = input.value.trim();
    
    if (!messageText) {
        return;
    }
    
    // Create new message element
    const messagesThread = document.getElementById('messages-thread');
    const newMessage = document.createElement('div');
    newMessage.className = 'message sent';
    
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    
    newMessage.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="message-time">Today, ${timeStr}</span>
            </div>
            <p class="message-text">${messageText}</p>
        </div>
    `;
    
    messagesThread.appendChild(newMessage);
    
    // Clear input
    input.value = '';
    
    // Scroll to bottom
    messagesThread.scrollTop = messagesThread.scrollHeight;
    
    // TODO: Send message to backend
    console.log('Sending message:', messageText);
}

// Send on Enter key (Shift+Enter for new line)
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('message-input');
    if (input) {
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});

// New message - open modal
function newMessage() {
    document.getElementById('new-message-modal').style.display = 'flex';
    setTimeout(() => {
        document.getElementById('new-message-username').focus();
    }, 100);
}

// Close modal
function closeNewMessageModal() {
    document.getElementById('new-message-modal').style.display = 'none';
    document.getElementById('new-message-username').value = '';
}

// Start new chat from modal
function startNewChat() {
    const username = document.getElementById('new-message-username').value.trim();
    
    if (!username) {
        alert('Please enter a username');
        return;
    }
    
    // Check if conversation already exists
    const conversations = document.querySelectorAll('.conversation-item');
    let exists = false;
    conversations.forEach(conv => {
        if (conv.querySelector('.conv-name').textContent.toLowerCase().includes(username.toLowerCase())) {
            exists = true;
            conv.click(); // Open existing conversation
        }
    });
    
    if (exists) {
        closeNewMessageModal();
        return;
    }
    
    // Create new conversation
    const convList = document.querySelector('.conversations-list');
    const newConv = document.createElement('div');
    newConv.className = 'conversation-item active';
    newConv.onclick = function() { openConversation(Date.now()); };
    
    newConv.innerHTML = `
        <div class="conv-avatar">👤</div>
        <div class="conv-info">
            <div class="conv-header">
                <span class="conv-name">${username}</span>
                <span class="conv-time">Just now</span>
            </div>
            <p class="conv-preview">Start a new conversation...</p>
        </div>
    `;
    
    // Remove active from all other conversations
    conversations.forEach(c => c.classList.remove('active'));
    
    // Add to top of list
    convList.insertBefore(newConv, convList.firstChild);
    
    // Update thread view
    document.querySelector('.thread-avatar').textContent = '👤';
    document.querySelector('.thread-info h3').textContent = username;
    document.querySelector('.thread-info p').textContent = 'User';
    
    // Clear messages
    document.getElementById('messages-thread').innerHTML = `
        <div style="text-align: center; padding: 40px; color: var(--text-muted);">
            <p>No messages yet. Start the conversation!</p>
        </div>
    `;
    
    closeNewMessageModal();
}

// Enter key to start chat in modal
document.addEventListener('DOMContentLoaded', function() {
    const usernameInput = document.getElementById('new-message-username');
    if (usernameInput) {
        usernameInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                startNewChat();
            }
        });
    }
});

console.log('Messages loaded successfully');