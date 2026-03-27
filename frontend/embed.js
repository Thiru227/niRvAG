/* ============================================
   niRvAG — Embeddable Chat Widget
   Usage: <script src="https://YOUR-DOMAIN/embed.js" data-server="https://YOUR-DOMAIN"></script>
   ============================================ */
(function () {
  const script = document.currentScript;
  const SERVER = (script && script.getAttribute('data-server')) || window.location.origin;
  const API = SERVER + '/api';

  // ── Inject Google Font ──
  const font = document.createElement('link');
  font.rel = 'stylesheet';
  font.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap';
  document.head.appendChild(font);

  // ── Inject Widget Styles ──
  const style = document.createElement('style');
  style.textContent = `
    #nirvag-widget-fab {
      position: fixed; bottom: 24px; right: 24px; z-index: 99999;
      width: 56px; height: 56px; border-radius: 50%;
      background: #18181b; color: #fafafa; border: none; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 20px rgba(0,0,0,0.25);
      transition: transform 0.2s, box-shadow 0.2s;
      font-family: 'Inter', system-ui, sans-serif;
    }
    #nirvag-widget-fab:hover { transform: scale(1.08); box-shadow: 0 6px 28px rgba(0,0,0,0.35); }
    #nirvag-widget-fab svg { width: 24px; height: 24px; }
    #nirvag-widget-panel {
      position: fixed; bottom: 92px; right: 24px; z-index: 99999;
      width: 380px; max-height: 560px; border-radius: 16px;
      background: #fff; border: 1px solid #e4e4e7;
      box-shadow: 0 8px 40px rgba(0,0,0,0.15);
      display: none; flex-direction: column; overflow: hidden;
      font-family: 'Inter', system-ui, sans-serif; font-size: 14px; color: #18181b;
    }
    #nirvag-widget-panel.open { display: flex; animation: nirvag-slide-up 0.25s ease-out; }
    @keyframes nirvag-slide-up { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
    .nirvag-header {
      background: #18181b; color: #fafafa; padding: 16px;
      display: flex; align-items: center; gap: 12px; flex-shrink: 0;
    }
    .nirvag-header-avatar {
      width: 36px; height: 36px; border-radius: 50%;
      background: rgba(255,255,255,0.15); display: flex; align-items: center; justify-content: center;
    }
    .nirvag-header-avatar svg { width: 20px; height: 20px; }
    .nirvag-header-info { flex: 1; }
    .nirvag-header-info div:first-child { font-weight: 600; font-size: 14px; }
    .nirvag-header-info div:last-child { font-size: 11px; opacity: 0.75; }
    .nirvag-close { background: none; border: none; color: #fafafa; cursor: pointer; opacity: 0.7; }
    .nirvag-close:hover { opacity: 1; }
    .nirvag-close svg { width: 18px; height: 18px; }
    .nirvag-body { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; background: #fafafa; min-height: 280px; max-height: 380px; }
    .nirvag-msg { display: flex; }
    .nirvag-msg.user { justify-content: flex-end; }
    .nirvag-msg.bot { justify-content: flex-start; }
    .nirvag-bubble {
      max-width: 80%; padding: 10px 14px; border-radius: 16px; font-size: 13px; line-height: 1.5;
      word-wrap: break-word; overflow-wrap: break-word;
    }
    .nirvag-msg.user .nirvag-bubble { background: #18181b; color: #fafafa; border-bottom-right-radius: 4px; }
    .nirvag-msg.bot .nirvag-bubble { background: #fff; border: 1px solid #e4e4e7; border-bottom-left-radius: 4px; }
    .nirvag-bubble strong { font-weight: 600; }
    .nirvag-bubble em { font-style: italic; }
    .nirvag-bubble ol, .nirvag-bubble ul { margin: 6px 0; padding-left: 20px; }
    .nirvag-bubble li { margin: 2px 0; }
    .nirvag-bubble ol { list-style-type: decimal; }
    .nirvag-bubble ul { list-style-type: disc; }
    .nirvag-time { font-size: 10px; color: #a1a1aa; margin-top: 2px; padding: 0 4px; }
    .nirvag-msg.user .nirvag-time { text-align: right; }
    .nirvag-footer {
      border-top: 1px solid #e4e4e7; padding: 12px; display: flex; gap: 8px; flex-shrink: 0; background: #fff;
    }
    .nirvag-footer input {
      flex: 1; border: 1px solid #e4e4e7; border-radius: 8px; padding: 8px 12px;
      font-size: 13px; outline: none; font-family: inherit; background: #fafafa;
    }
    .nirvag-footer input:focus { border-color: #18181b; box-shadow: 0 0 0 2px rgba(24,24,27,0.1); }
    .nirvag-footer button {
      width: 36px; height: 36px; border-radius: 8px; border: none;
      background: #18181b; color: #fafafa; cursor: pointer; display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .nirvag-footer button:hover { background: #27272a; }
    .nirvag-footer button svg { width: 16px; height: 16px; }
    .nirvag-prechat { padding: 24px; display: flex; flex-direction: column; gap: 12px; flex: 1; justify-content: center; }
    .nirvag-prechat h3 { font-weight: 600; font-size: 16px; margin: 0; }
    .nirvag-prechat p { font-size: 13px; color: #71717a; margin: 0 0 8px 0; }
    .nirvag-prechat label { font-size: 12px; font-weight: 500; margin-bottom: 2px; display: block; }
    .nirvag-prechat input {
      width: 100%; border: 1px solid #e4e4e7; border-radius: 8px; padding: 8px 12px;
      font-size: 13px; outline: none; font-family: inherit; box-sizing: border-box;
    }
    .nirvag-prechat input:focus { border-color: #18181b; }
    .nirvag-prechat button {
      width: 100%; padding: 10px; border-radius: 8px; border: none;
      background: #18181b; color: #fafafa; font-weight: 500; font-size: 13px;
      cursor: pointer; font-family: inherit; margin-top: 4px;
    }
    .nirvag-prechat button:hover { background: #27272a; }
    .nirvag-typing { display: flex; gap: 4px; padding: 10px 14px; }
    .nirvag-typing-dot {
      width: 6px; height: 6px; border-radius: 50%; background: #a1a1aa;
      animation: nirvag-bounce 1.4s infinite ease-in-out;
    }
    .nirvag-typing-dot:nth-child(2) { animation-delay: 0.16s; }
    .nirvag-typing-dot:nth-child(3) { animation-delay: 0.32s; }
    @keyframes nirvag-bounce {
      0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); }
    }
    .nirvag-powered { text-align: center; font-size: 10px; color: #a1a1aa; padding: 6px; background: #fff; }
    .nirvag-powered a { color: #71717a; text-decoration: none; font-weight: 500; }
    @media (max-width: 480px) {
      #nirvag-widget-panel { width: calc(100vw - 24px); right: 12px; bottom: 80px; max-height: 70vh; }
      #nirvag-widget-fab { bottom: 16px; right: 16px; }
    }
  `;
  document.head.appendChild(style);

  // ── SVG Icons ──
  const ICON_CHAT = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"/></svg>';
  const ICON_X = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>';
  const ICON_SEND = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>';
  const ICON_BOT = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>';

  // ── Create FAB ──
  const fab = document.createElement('button');
  fab.id = 'nirvag-widget-fab';
  fab.innerHTML = ICON_CHAT;
  fab.title = 'Chat with niRvAG Support';
  document.body.appendChild(fab);

  // ── Create Panel ──
  const panel = document.createElement('div');
  panel.id = 'nirvag-widget-panel';
  panel.innerHTML = `
    <div class="nirvag-header">
      <div class="nirvag-header-avatar">${ICON_BOT}</div>
      <div class="nirvag-header-info">
        <div>niRvAG Support</div>
        <div>● Online — typically replies instantly</div>
      </div>
      <button class="nirvag-close" id="nirvag-close">${ICON_X}</button>
    </div>
    <div id="nirvag-prechat" class="nirvag-prechat">
      <h3>Welcome! 👋</h3>
      <p>Please enter your details to start chatting with our support team.</p>
      <div>
        <label>Name *</label>
        <input type="text" id="nirvag-w-name" placeholder="Your name" required>
      </div>
      <div>
        <label>Email *</label>
        <input type="email" id="nirvag-w-email" placeholder="you@example.com" required>
      </div>
      <button id="nirvag-w-start">Start Chat</button>
    </div>
    <div id="nirvag-messages" class="nirvag-body" style="display:none;"></div>
    <div id="nirvag-input-area" class="nirvag-footer" style="display:none;">
      <input type="text" id="nirvag-w-input" placeholder="Type your message..." autocomplete="off">
      <button id="nirvag-w-send">${ICON_SEND}</button>
    </div>
    <div class="nirvag-powered">Powered by <a href="${SERVER}" target="_blank">niRvAG</a></div>
  `;
  document.body.appendChild(panel);

  // ── State ──
  let isOpen = false;
  let sessionId = null;
  let wName = '';
  let wEmail = '';

  // ── Markdown Renderer ──
  function md(text) {
    let h = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    h = h.replace(/\*(.+?)\*/g, '<em>$1</em>');
    h = h.replace(/`(.+?)`/g, '<code>$1</code>');
    h = h.replace(/^(\d+)\.\s+(.+)$/gm, '<li>$2</li>');
    h = h.replace(/(<li>.*<\/li>\n?)+/g, function(m) {
      if (m.indexOf('list-disc') === -1) return '<ol>' + m + '</ol>';
      return m;
    });
    h = h.replace(/^[•\-]\s+(.+)$/gm, '<li class="list-disc">$1</li>');
    h = h.replace(/(<li class="list-disc">.*<\/li>\n?)+/g, function(m) { return '<ul>' + m + '</ul>'; });
    h = h.replace(/\n/g, '<br>');
    h = h.replace(/<br><\/li>/g, '</li>');
    h = h.replace(/<\/ol><br>/g, '</ol>');
    h = h.replace(/<\/ul><br>/g, '</ul>');
    return h;
  }

  // ── Toggle ──
  fab.addEventListener('click', function () {
    isOpen = !isOpen;
    if (isOpen) {
      panel.classList.add('open');
      fab.innerHTML = ICON_X;
    } else {
      panel.classList.remove('open');
      fab.innerHTML = ICON_CHAT;
    }
  });
  document.getElementById('nirvag-close').addEventListener('click', function () {
    isOpen = false;
    panel.classList.remove('open');
    fab.innerHTML = ICON_CHAT;
  });

  // ── Start Chat ──
  document.getElementById('nirvag-w-start').addEventListener('click', function () {
    wName = document.getElementById('nirvag-w-name').value.trim();
    wEmail = document.getElementById('nirvag-w-email').value.trim();
    if (!wName || !wEmail) { alert('Please enter both name and email.'); return; }
    document.getElementById('nirvag-prechat').style.display = 'none';
    document.getElementById('nirvag-messages').style.display = 'flex';
    document.getElementById('nirvag-input-area').style.display = 'flex';
    addBotMsg('Hello ' + wName + '! 👋 Welcome to **niRvAG Support**. How can I help you today?');
    document.getElementById('nirvag-w-input').focus();
  });

  // ── Send Message ──
  function sendMsg() {
    const input = document.getElementById('nirvag-w-input');
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';
    addUserMsg(msg);
    showTyping();

    fetch(API + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, user_name: wName, user_email: wEmail, session_id: sessionId })
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        removeTyping();
        sessionId = data.session_id || sessionId;
        addBotMsg(data.reply || data.response || 'Sorry, something went wrong.');
      })
      .catch(function () {
        removeTyping();
        addBotMsg("I'm having trouble connecting right now. Please try again in a moment.");
      });
  }

  document.getElementById('nirvag-w-send').addEventListener('click', sendMsg);
  document.getElementById('nirvag-w-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') sendMsg();
  });

  // ── Message Helpers ──
  function addUserMsg(text) {
    const el = document.getElementById('nirvag-messages');
    const t = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.className = 'nirvag-msg user';
    div.innerHTML = '<div><div class="nirvag-bubble">' + text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</div><div class="nirvag-time">' + t + '</div></div>';
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;
  }

  function addBotMsg(text) {
    const el = document.getElementById('nirvag-messages');
    const t = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.className = 'nirvag-msg bot';
    div.innerHTML = '<div><div class="nirvag-bubble">' + md(text) + '</div><div class="nirvag-time">' + t + '</div></div>';
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;
  }

  function showTyping() {
    const el = document.getElementById('nirvag-messages');
    const div = document.createElement('div');
    div.id = 'nirvag-typing';
    div.className = 'nirvag-msg bot';
    div.innerHTML = '<div class="nirvag-bubble nirvag-typing"><div class="nirvag-typing-dot"></div><div class="nirvag-typing-dot"></div><div class="nirvag-typing-dot"></div></div>';
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;
  }

  function removeTyping() {
    var t = document.getElementById('nirvag-typing');
    if (t) t.remove();
  }
})();
