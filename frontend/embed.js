/* ============================================
   NIRVAG — Embeddable Chat Widget
   Usage: <script src="https://your-nirvag-url.com/embed.js" data-server="https://your-nirvag-url.com"></script>
   ============================================ */
(function() {
  const script = document.currentScript;
  const SERVER = script?.getAttribute('data-server') || window.location.origin;

  // Inject CSS
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = `${SERVER}/css/variables.css`;
  document.head.appendChild(link);

  const link2 = document.createElement('link');
  link2.rel = 'stylesheet';
  link2.href = `${SERVER}/css/chat.css`;
  document.head.appendChild(link2);

  // Font
  const font = document.createElement('link');
  font.rel = 'stylesheet';
  font.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap';
  document.head.appendChild(font);

  // Load API base
  window.API_BASE = `${SERVER}/api`;

  // Load chat.js
  const chatScript = document.createElement('script');
  chatScript.src = `${SERVER}/js/chat.js`;
  document.body.appendChild(chatScript);
})();
