/* ============================================
   NIRVAG — Chat Widget Logic
   Fetches bot name/avatar from settings API
   ============================================ */
(function () {
  let sessionId = null;
  let chatOpen = false;
  let chatStarted = false;
  let userName = '';
  let userEmail = '';
  let botName = 'niRvAG Support';
  let botAvatar = '';
  let welcomeMsg = 'Hello! 👋 How can I help you today?';

  // ── Load settings before rendering ──
  async function loadBotSettings() {
    try {
      const base = (typeof API_BASE !== 'undefined') ? API_BASE : '/api';
      const r = await fetch(`${base.replace('/api','')}/api/widget/settings`);
      if (r.ok) {
        const s = await r.json();
        botName = s.brand_name ? `${s.brand_name} Support` : 'niRvAG Support';
        botAvatar = s.logo_url || '';
        welcomeMsg = s.welcome_message || welcomeMsg;
        if (s.color_primary) {
          document.querySelector('.chat-fab')?.style.setProperty('background', s.color_primary);
        }
      }
    } catch (e) { /* Use defaults */ }
  }

  function getAvatarHTML() {
    if (botAvatar) return `<img src="${botAvatar}" alt="${botName}">`;
    return botName[0].toUpperCase();
  }

  // ── Build Widget DOM ──
  function initWidget() {
    // FAB
    const fab = document.createElement('button');
    fab.className = 'chat-fab';
    fab.id = 'chatFab';
    fab.innerHTML = '💬';
    fab.onclick = toggleChat;
    document.body.appendChild(fab);

    // Widget
    const widget = document.createElement('div');
    widget.className = 'chat-widget';
    widget.id = 'chatWidget';
    widget.innerHTML = `
      <div class="chat-header">
        <div class="chat-header-avatar" id="chatBotAvatar">${getAvatarHTML()}</div>
        <div class="chat-header-info">
          <div class="chat-header-name" id="chatBotName">${botName}</div>
          <div class="chat-header-status">● Online — typically replies instantly</div>
        </div>
      </div>
      <div id="chatBody">
        <div class="chat-prechat" id="chatPrechat">
          <h3>Welcome! 👋</h3>
          <p>Tell us who you are and we'll get you connected with AI support.</p>
          <div class="form-group">
            <label class="form-label">Your Name</label>
            <input type="text" class="form-input" id="chatName" placeholder="e.g. Priya">
          </div>
          <div class="form-group">
            <label class="form-label">Your Email</label>
            <input type="email" class="form-input" id="chatEmail" placeholder="e.g. priya@example.com">
          </div>
          <button class="btn btn-primary w-full" onclick="startChat()" style="margin-top:8px">Start Chat →</button>
        </div>
      </div>
    `;
    document.body.appendChild(widget);
  }

  function toggleChat() {
    chatOpen = !chatOpen;
    const widget = document.getElementById('chatWidget');
    const fab = document.getElementById('chatFab');
    if (chatOpen) {
      widget.classList.add('open');
      fab.innerHTML = '✕';
      fab.classList.add('active');
    } else {
      widget.classList.remove('open');
      fab.innerHTML = '💬';
      fab.classList.remove('active');
    }
  }

  // Expose startChat globally
  window.startChat = function () {
    userName = document.getElementById('chatName').value.trim() || 'Customer';
    userEmail = document.getElementById('chatEmail').value.trim();
    if (!userEmail) { alert('Please enter your email'); return; }

    chatStarted = true;
    const body = document.getElementById('chatBody');
    body.innerHTML = `
      <div class="chat-messages" id="chatMessages"></div>
      <div class="chat-input-area">
        <input type="text" id="chatInput" placeholder="Type your message..." onkeydown="if(event.key==='Enter')sendMsg()">
        <button class="chat-send" id="chatSendBtn" onclick="sendMsg()">➤</button>
      </div>
    `;

    // Welcome message
    addMessage('bot', welcomeMsg);
    document.getElementById('chatInput').focus();
  };

  window.sendMsg = async function () {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    addMessage('user', message);
    showTyping();

    try {
      const API_URL = (typeof API_BASE !== 'undefined') ? API_BASE : '/api';
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message, session_id: sessionId,
          user_name: userName, user_email: userEmail
        })
      });
      const data = await res.json();
      hideTyping();

      sessionId = data.session_id;
      addMessage('bot', data.reply);

      if (data.ticket_created && data.ticket) {
        addTicketCard(data.ticket);
      }
    } catch (e) {
      hideTyping();
      addMessage('bot', 'Sorry, something went wrong. Please try again.');
    }
  };

  function addMessage(role, text) {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    const now = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.innerHTML = `<div class="msg-bubble">${text}</div><div class="msg-time">${now}</div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  function addTicketCard(ticket) {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    const div = document.createElement('div');
    div.className = 'msg bot';
    div.innerHTML = `
      <div class="ticket-card-widget">
        <div class="tcw-header">
          <div class="tcw-title">✅ Ticket Created <span class="badge badge-primary">#${ticket.ticket_number || ''}</span></div>
        </div>
        <div class="tcw-row"><span class="tcw-label">Priority</span><span class="tcw-value"><span class="badge priority-${ticket.priority}">${ticket.priority}</span></span></div>
        ${ticket.assigned_to_name ? `<div class="tcw-row"><span class="tcw-label">Agent</span><span class="tcw-value">${ticket.assigned_to_name}</span></div>` : ''}
        <div class="tcw-row"><span class="tcw-label">Status</span><span class="tcw-value"><span class="badge status-open">Open</span></span></div>
      </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  function showTyping() {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    const el = document.createElement('div');
    el.id = 'typingIndicator';
    el.className = 'msg bot';
    el.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
  }

  function hideTyping() {
    document.getElementById('typingIndicator')?.remove();
  }

  // ── Boot ──
  async function boot() {
    await loadBotSettings();
    initWidget();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
