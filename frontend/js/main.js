// Global Configuration
const BACKEND_URL = window.location.origin;


// Mobile Navbar Hamburger Toggle
document.addEventListener('DOMContentLoaded', () => {
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const navLinks = document.getElementById('nav-links');

    if (hamburgerBtn && navLinks) {
        hamburgerBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            hamburgerBtn.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!hamburgerBtn.contains(e.target) && !navLinks.contains(e.target)) {
                navLinks.classList.remove('active');
                hamburgerBtn.classList.remove('active');
            }
        });
    }

    // Theme Toggle
    const toggleBtn = document.getElementById('theme-toggle');
    const body = document.body;

    if (toggleBtn) {
        // Check saved preference
        if (localStorage.getItem('theme') === 'dark') {
            body.classList.add('dark-mode');
        }

        toggleBtn.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            localStorage.setItem('theme', body.classList.contains('dark-mode') ? 'dark' : 'light');
        });
    }

    // Initialize Floating Chatbot Widget
    initChatbot();
});

// AI Chatbot Widget Logic
function initChatbot() {
    const chatBtn = document.getElementById('chat-button');
    const chatWin = document.getElementById('chat-window');
    const closeChat = document.getElementById('close-chat');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');

    if (!chatBtn || !chatWin) return;

    chatBtn.addEventListener('click', () => {
        chatWin.style.display = chatWin.style.display === 'none' ? 'flex' : 'none';
        if (chatWin.style.display === 'flex' && chatInput) {
            chatInput.focus();
        }
    });

    if (closeChat) {
        closeChat.addEventListener('click', () => {
            chatWin.style.display = 'none';
        });
    }

    async function sendMessage() {
        if (!chatInput || !chatMessages) return;
        const msg = chatInput.value.trim();
        if (!msg) return;

        // Append User Message
        chatMessages.innerHTML += `<div class="message-wrapper right"><div class="chat-message user-message">${escapeHTML(msg)}</div></div>`;
        chatInput.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Context Scraping
        let context = "No specific context available.";
        const pageTitle = document.querySelector('h1')?.innerText;
        const cards = Array.from(document.querySelectorAll('.whatsapp-card, .instagram-card, .ps-card, .stat-card'));
        const stats = cards.map(c => c.innerText.replace(/\n\n/g, ': ').replace(/\n/g, ' ')).join('; ');
        if (pageTitle) {
            context = `Page Title/User: ${pageTitle}. Stats: ${stats}`;
        }

        const selectedUser = sessionStorage.getItem('whatsapp_selected_user') || 'Overall';
        const fileId = sessionStorage.getItem('whatsapp_file_id');

        // Show Typing Indicator
        const typingId = 'typing-' + Date.now();
        chatMessages.innerHTML += `<div id="${typingId}" class="message-wrapper left"><div class="chat-message bot-message typing">Typing...</div></div>`;
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch(`${BACKEND_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: msg, 
                    context: context, 
                    selected_user: selectedUser,
                    file_id: fileId 
                })
            });
            const data = await response.json();

            const typingEl = document.getElementById(typingId);
            if (typingEl) typingEl.remove();

            // Append Bot Message
            let botMsg = data.response.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
            chatMessages.innerHTML += `<div class="message-wrapper left"><div class="chat-message bot-message">${botMsg}</div></div>`;
            chatMessages.scrollTop = chatMessages.scrollHeight;

        } catch (error) {
            console.error("Chat Error:", error);
            const typingEl = document.getElementById(typingId);
            if (typingEl) typingEl.remove();
            chatMessages.innerHTML += `<div class="message-wrapper left"><div class="chat-message bot-message error">Error connecting to bot.</div></div>`;
        }
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }
}

// Utility to sanitize HTML
function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}
