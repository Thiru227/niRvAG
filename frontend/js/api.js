/* ============================================
   NIRVAG — API Service
   ============================================ */

const API_BASE = (window.location.port === '8080')
  ? 'http://127.0.0.1:5000/api'
  : `${window.location.origin}/api`;

const API = {
  /** Generic fetch wrapper */
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const token = localStorage.getItem('nirvag_token');

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        // Auto-logout on 401/403 — stale token
        if (response.status === 401 || response.status === 403) {
          const path = window.location.pathname;
          if (path.includes('admin') || path.includes('attendee')) {
            Auth.clear();
            window.location.href = '/pages/login.html';
            return;
          }
        }
        throw { status: response.status, message: data.error || 'Request failed', data };
      }

      return data;
    } catch (err) {
      if (err.status) throw err;
      console.error('API Error:', err);
      throw { status: 0, message: 'Network error. Please check your connection.' };
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  },

  post(endpoint, body) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  patch(endpoint, body) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  },

  /** Upload file (multipart) */
  async upload(endpoint, formData) {
    const url = `${API_BASE}${endpoint}`;
    const token = localStorage.getItem('nirvag_token');

    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData, // browser sets Content-Type multipart automatically
    });

    const data = await response.json();
    if (!response.ok) {
      throw { status: response.status, message: data.error || 'Upload failed', data };
    }
    return data;
  },

  // ─── Auth ───
  login(email, password) {
    return this.post('/auth/login', { email, password });
  },

  createSession(name, email) {
    return this.post('/auth/session', { name, email });
  },

  // ─── Chat ───
  sendChat(message, sessionId, userName, userEmail) {
    return this.post('/chat', { message, session_id: sessionId, user_name: userName, user_email: userEmail });
  },

  // ─── Tickets ───
  getTickets(params = '') {
    return this.get(`/tickets${params}`);
  },

  getTicket(id) {
    return this.get(`/tickets/${id}`);
  },

  createTicket(data) {
    return this.post('/tickets', data);
  },

  updateTicket(id, data) {
    return this.patch(`/tickets/${id}`, data);
  },

  resolveTicket(id, data) {
    return this.post(`/tickets/${id}/resolve`, data);
  },

  escalateTicket(id, reason) {
    return this.post(`/tickets/${id}/escalate`, { reason });
  },

  getTicketEvents(id) {
    return this.get(`/tickets/${id}/events`);
  },

  // ─── Admin ───
  getUsers() {
    return this.get('/admin/users');
  },

  createUser(data) {
    return this.post('/admin/users', data);
  },

  updateUser(id, data) {
    return this.patch(`/admin/users/${id}`, data);
  },

  deleteUser(id) {
    return this.delete(`/admin/users/${id}`);
  },

  getSettings() {
    return this.get('/admin/settings');
  },

  updateSettings(data) {
    return this.post('/admin/settings', data);
  },

  getAnalytics() {
    return this.get('/admin/analytics');
  },

  // ─── Upload ───
  uploadProducts(formData) {
    return this.upload('/upload/products', formData);
  },

  uploadDocument(formData) {
    return this.upload('/upload/document', formData);
  },

  uploadVoice(formData) {
    return this.upload('/voice/upload', formData);
  },
};

/* ── Auth State Helper ── */
const Auth = {
  getToken() {
    return localStorage.getItem('nirvag_token');
  },

  getUser() {
    const u = localStorage.getItem('nirvag_user');
    return u ? JSON.parse(u) : null;
  },

  setAuth(token, user) {
    localStorage.setItem('nirvag_token', token);
    localStorage.setItem('nirvag_user', JSON.stringify(user));
  },

  clear() {
    localStorage.removeItem('nirvag_token');
    localStorage.removeItem('nirvag_user');
  },

  isLoggedIn() {
    return !!this.getToken();
  },

  getRole() {
    const user = this.getUser();
    return user ? user.role : null;
  },

  requireAuth(roles = []) {
    if (!this.isLoggedIn()) {
      window.location.href = '/pages/login.html';
      return false;
    }
    if (roles.length > 0 && !roles.includes(this.getRole())) {
      window.location.href = '/pages/login.html';
      return false;
    }
    return true;
  }
};

/* ── Toast Notifications ── */
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}</span>
    <span class="toast-msg">${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/* ── Utility: Format time ── */
function formatTime(date) {
  return new Date(date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function formatDate(date) {
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatRelative(date) {
  const now = new Date();
  const d = new Date(date);
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHr = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return formatDate(date);
}

/* ── Priority/Status/Sentiment helpers ── */
function getPriorityClass(priority) {
  return `priority-${priority}`;
}

function getStatusClass(status) {
  return `status-${status}`;
}

function getSentimentEmoji(sentiment) {
  const map = { 
    happy: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline text-green-500 mr-1"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/></svg>', 
    neutral: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline text-slate-500 mr-1"><circle cx="12" cy="12" r="10"/><line x1="8" x2="16" y1="15" y2="15"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/></svg>', 
    frustrated: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline text-amber-500 mr-1"><circle cx="12" cy="12" r="10"/><path d="M16 16s-1.5-2-4-2-4 2-4 2"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/></svg>', 
    angry: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline text-red-500 mr-1"><circle cx="12" cy="12" r="10"/><path d="M16 16s-1.5-2-4-2-4 2-4 2"/><path d="M7.5 8 10 9"/><path d="M14 9l2.5-1"/><line x1="9" x2="9.01" y1="12" y2="12"/><line x1="15" x2="15.01" y1="12" y2="12"/></svg>' 
  };
  return map[sentiment] || map.neutral;
}

function getPriorityEmoji(priority) {
  const map = { low: 'Low', medium: 'Medium', high: 'High', critical: 'Critical' };
  return map[priority] || '🟡';
}

function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}
