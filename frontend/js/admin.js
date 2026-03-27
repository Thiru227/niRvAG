/* ============================================
   NIRVAG — Admin Dashboard Logic
   ============================================ */

// ── Team category labels ──
const TEAM_LABELS = {
  'order_shipping': '🚚 Order & Shipping',
  'billing_payments': '💳 Billing & Payments',
  'technical_support': '🔧 Technical Support',
  'product_inquiries': '📦 Product Inquiries',
  'general_support': '💬 General Support'
};

const TEAM_KEYWORDS = {
  'order_shipping': 'order, shipping, delivery, tracking, dispatch',
  'billing_payments': 'payment, refund, billing, invoice, transaction',
  'technical_support': 'bug, error, technical, crash, login, password, account',
  'product_inquiries': 'product, feature, catalog, recommendation, warranty, return',
  'general_support': 'general, support, help, feedback, account, info'
};

function getTeamLabel(expertise) {
  if (!expertise) return '—';
  const expertiseLower = expertise.toLowerCase();
  for (const [key, label] of Object.entries(TEAM_LABELS)) {
    const keywords = TEAM_KEYWORDS[key].split(', ');
    if (keywords.some(kw => expertiseLower.includes(kw))) return label;
  }
  return expertise || '—';
}

// ── Pagination State ──
const PAGE_SIZE = 5;
const paginationState = {
  products: { data: [], page: 1 },
  documents: { data: [], page: 1 },
  users: { data: [], page: 1 },
};

function renderPagination(containerId, stateKey, renderFn) {
  const state = paginationState[stateKey];
  const totalPages = Math.ceil(state.data.length / PAGE_SIZE) || 1;
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `
    <div class="flex items-center justify-between px-4 py-3 border-t">
      <span class="text-xs text-muted-foreground">Page ${state.page} of ${totalPages} (${state.data.length} items)</span>
      <div class="flex gap-2">
        <button class="inline-flex items-center justify-center rounded-md text-xs font-medium border h-8 px-3 transition-colors ${state.page <= 1 ? 'opacity-40 cursor-not-allowed' : 'hover:bg-muted'}" ${state.page <= 1 ? 'disabled' : ''}
          onclick="paginationState.${stateKey}.page--; ${renderFn}()">← Prev</button>
        <button class="inline-flex items-center justify-center rounded-md text-xs font-medium border h-8 px-3 transition-colors ${state.page >= totalPages ? 'opacity-40 cursor-not-allowed' : 'hover:bg-muted'}" ${state.page >= totalPages ? 'disabled' : ''}
          onclick="paginationState.${stateKey}.page++; ${renderFn}()">Next →</button>
      </div>
    </div>
  `;
}

function getPageSlice(stateKey) {
  const state = paginationState[stateKey];
  const start = (state.page - 1) * PAGE_SIZE;
  return state.data.slice(start, start + PAGE_SIZE);
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  if (!Auth.requireAuth(['admin'])) return;
  const user = Auth.getUser();
  document.getElementById('userName').textContent = user?.name || 'Admin';
  document.getElementById('userEmail').textContent = user?.email || '';
  document.getElementById('userAvatar').textContent = (user?.name || 'A')[0].toUpperCase();
  document.getElementById('greeting').textContent = `Hello, ${(user?.name || 'Admin').split(' ')[0]}! 👋`;

  // Load theme
  const saved = localStorage.getItem('nirvag_theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  document.getElementById('themeBtn')?.setAttribute('data-theme', saved);

  loadDashboard();
  loadSettings();
});

// ── Theme ──
function toggleTheme() {
  const curr = document.documentElement.getAttribute('data-theme');
  const next = curr === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('nirvag_theme', next);
  // Toggle dark class for Tailwind
  if (next === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}

// ── Panel Navigation ──
function switchPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.add('hidden'));
  document.getElementById(`panel-${name}`).classList.remove('hidden');
  document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('bg-muted', 'text-foreground'));
  document.querySelectorAll('.sidebar-link').forEach(l => l.classList.add('text-muted-foreground'));
  const activeLink = document.querySelector(`[data-panel="${name}"]`);
  if(activeLink) {
    activeLink.classList.remove('text-muted-foreground');
    activeLink.classList.add('bg-muted', 'text-foreground');
  }

  if (name === 'tickets') loadTickets();
  if (name === 'users') loadUsers();
  if (name === 'orders') loadOrders();
  if (name === 'settings') loadSettings();
  if (name === 'products') loadProducts();
  if (name === 'documents') loadDocuments();
}

// ── Dashboard ──
async function loadDashboard() {
  try {
    const data = await API.getAnalytics();
    document.getElementById('metricTotal').textContent = data.total_tickets || 0;
    document.getElementById('metricOpen').textContent = data.open || 0;
    document.getElementById('metricEscalated').textContent = data.escalated || 0;
    document.getElementById('metricClosed').textContent = data.closed || 0;
    document.getElementById('ticketCountBadge').textContent = data.open || 0;

    renderSentiment(data.sentiment_breakdown || {});
    renderIntents(data.top_intents || []);
  } catch (e) {
    console.error('Analytics error:', e);
  }
}

function renderSentiment(data) {
  const el = document.getElementById('sentimentBars');
  const total = Object.values(data).reduce((a, b) => a + b, 0) || 1;
  const order = ['happy', 'neutral', 'frustrated', 'angry'];
  const labels = { happy: 'Happy', neutral: 'Neutral', frustrated: 'Frustrated', angry: 'Angry' };
  const colors = { happy: '#22c55e', neutral: '#64748b', frustrated: '#f59e0b', angry: '#ef4444' };

  el.innerHTML = order.map(k => `
    <div class="flex items-center gap-3">
      <div class="text-sm w-28 text-muted-foreground">${labels[k]}</div>
      <div class="flex-1 bg-muted rounded-full h-2.5 overflow-hidden">
        <div class="h-full rounded-full transition-all duration-500" style="width:${((data[k]||0)/total*100)}%; background:${colors[k]}"></div>
      </div>
      <div class="text-sm font-medium w-8 text-right">${data[k]||0}</div>
    </div>
  `).join('');
}

function renderIntents(intents) {
  const el = document.getElementById('intentBars');
  if (!intents.length) { el.innerHTML = '<div class="text-sm text-muted-foreground text-center">No intents yet</div>'; return; }
  const max = intents[0]?.count || 1;
  el.innerHTML = intents.slice(0, 8).map(i => `
    <div class="flex items-center gap-3">
      <div class="text-sm w-28 truncate text-muted-foreground capitalize">${i.intent.replace(/_/g, ' ')}</div>
      <div class="flex-1 bg-muted rounded-full h-2.5 overflow-hidden">
        <div class="h-full rounded-full bg-primary/70 transition-all duration-500" style="width:${(i.count/max*100)}%"></div>
      </div>
      <div class="text-sm font-medium w-8 text-right">${i.count}</div>
    </div>
  `).join('');
}

// ── Tickets ──
let allTickets = [];
async function loadTickets() {
  try {
    const tickets = await API.getTickets();
    allTickets = tickets;
    renderTickets(tickets);
  } catch (e) { console.error(e); }
}

function filterTickets(status, btn) {
  // Legacy
}
window.filterTicketsCore = function(status) {
  if (status === 'all') return renderTickets(allTickets);
  renderTickets(allTickets.filter(t => t.status === status));
};

function renderTickets(tickets) {
  const tbody = document.getElementById('ticketsTableBody');
  if (!tickets.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="p-8 text-center text-muted-foreground"><div class="text-2xl mb-2">🎫</div><div class="font-medium">No tickets found</div></td></tr>';
    return;
  }
  tbody.innerHTML = tickets.map(t => `
    <tr class="border-b transition-colors hover:bg-muted/50 cursor-pointer" onclick="viewTicket('${t.id}')">
      <td class="p-4 align-middle"><strong>#${t.ticket_number || '—'}</strong></td>
      <td class="p-4 align-middle truncate max-w-[200px]">${escapeHtml(t.title)}</td>
      <td class="p-4 align-middle">${escapeHtml(t.user_name)}<br><span class="text-xs text-muted-foreground">${escapeHtml(t.user_email)}</span></td>
      <td class="p-4 align-middle"><span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold tracking-wide uppercase ${t.priority==='critical'?'text-destructive border-destructive/20 bg-destructive/10':t.priority==='high'?'text-yellow-600 bg-yellow-50 border-yellow-200':'text-primary bg-primary/10 border-primary/20'}">${t.priority}</span></td>
      <td class="p-4 align-middle"><span class="inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold">${t.status.replace('_', ' ')}</span></td>
      <td class="p-4 align-middle text-sm text-muted-foreground">${formatRelative(t.created_at)}</td>
      <td class="p-4 align-middle"><button class="inline-flex items-center justify-center rounded-md text-xs font-medium transition-colors hover:bg-muted h-8 px-3 border" onclick="event.stopPropagation();viewTicket('${t.id}')">View →</button></td>
    </tr>
  `).join('');
}

async function viewTicket(id) {
  try {
    const ticket = await API.getTicket(id);
    let events = [];
    try { events = await API.getTicketEvents(id); } catch(e) {}

    document.getElementById('ticketDetailTitle').textContent = `Ticket #${ticket.ticket_number || ''} — ${ticket.title}`;
    document.getElementById('ticketDetailContent').innerHTML = `
      <div class="grid gap-6 md:grid-cols-3">
        <div class="md:col-span-2 space-y-6">
          <div class="rounded-lg border bg-muted/30 p-4">
            <div class="text-xs text-muted-foreground mb-2 font-medium uppercase tracking-wider">Description</div>
            <p class="text-sm leading-relaxed">${escapeHtml(ticket.description)}</p>
          </div>
          ${events && events.length > 0 ? `
            <div>
              <div class="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">Timeline</div>
              <div class="space-y-3">
                ${events.map(e => `
                  <div class="flex gap-3">
                    <div class="mt-1.5 flex-shrink-0 w-2 h-2 rounded-full bg-primary/40 ring-4 ring-primary/10"></div>
                    <div class="flex flex-col">
                      <span class="text-sm font-medium capitalize">${e.event_type.replace('_', ' ')} ${e.new_value ? '<span class=\"font-normal text-muted-foreground\">→ ' + e.new_value + '</span>' : ''}</span>
                      ${e.note ? `<span class="text-xs text-foreground/80 mt-0.5">${escapeHtml(e.note)}</span>` : ''}
                      <span class="text-xs text-muted-foreground mt-0.5">${formatRelative(e.created_at)} by ${e.actor_email}</span>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : '<div class="text-sm text-muted-foreground">No activity events yet.</div>'}
        </div>
        <div class="space-y-4">
          <div class="rounded-lg border p-4 space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-xs text-muted-foreground font-medium uppercase tracking-wider">Status</span>
              <span class="inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold">${ticket.status.replace('_',' ')}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-xs text-muted-foreground font-medium uppercase tracking-wider">Priority</span>
              <span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold tracking-wide uppercase ${ticket.priority==='critical'?'text-destructive border-destructive/20 bg-destructive/10':ticket.priority==='high'?'text-yellow-600 bg-yellow-50 border-yellow-200':'text-primary bg-primary/10 border-primary/20'}">${ticket.priority}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-xs text-muted-foreground font-medium uppercase tracking-wider">Sentiment</span>
              <span class="text-sm">${getSentimentEmoji(ticket.sentiment)} ${ticket.sentiment || 'neutral'}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-xs text-muted-foreground font-medium uppercase tracking-wider">Intent</span>
              <span class="text-sm capitalize">${(ticket.intent || 'other').replace(/_/g, ' ')}</span>
            </div>
          </div>
          <div class="rounded-lg border p-4 space-y-2">
            <div class="text-xs text-muted-foreground font-medium uppercase tracking-wider">Customer</div>
            <div class="text-sm font-medium">${escapeHtml(ticket.user_name)}</div>
            <div class="text-xs text-muted-foreground">${escapeHtml(ticket.user_email)}</div>
          </div>
          ${ticket.assigned_to_name ? `
            <div class="rounded-lg border p-4 space-y-2">
              <div class="text-xs text-muted-foreground font-medium uppercase tracking-wider">Assigned To</div>
              <div class="text-sm font-medium">${escapeHtml(ticket.assigned_to_name)}</div>
            </div>
          ` : ''}
          ${ticket.resolution_text ? `
            <div class="rounded-lg border border-green-200 bg-green-50 dark:bg-green-950/20 dark:border-green-900 p-4 space-y-2">
              <div class="text-xs text-green-700 dark:text-green-400 font-medium uppercase tracking-wider">Resolution</div>
              <div class="text-sm">${escapeHtml(ticket.resolution_text)}</div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
    openModal('ticketDetailModal');
    if(window.lucide) window.lucide.createIcons();
  } catch (e) {
    console.error('View ticket error:', e);
    showToast('Failed to load ticket', 'error');
  }
}

// ── Orders ──
async function loadOrders() {
  try {
    const data = await API.get('/orders');
    const orders = data.orders || [];
    const tbody = document.getElementById('ordersTableBody');
    if (!orders.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted p-4">No orders</td></tr>';
      return;
    }
    const statusColors = { delivered: 'text-green-700 bg-green-50 border-green-200', in_transit: 'text-blue-700 bg-blue-50 border-blue-200', shipped: 'text-blue-700 bg-blue-50 border-blue-200', processing: 'text-yellow-700 bg-yellow-50 border-yellow-200', cancelled: 'text-destructive bg-destructive/10 border-destructive/20', delayed: 'text-destructive bg-destructive/10 border-destructive/20' };
    tbody.innerHTML = orders.map(o => `
      <tr class="border-b transition-colors hover:bg-muted/50">
        <td class="p-4 align-middle"><strong>${o.order_id}</strong></td>
        <td class="p-4 align-middle">${o.customer_name}<br><span class="text-xs text-muted-foreground">${o.customer_email}</span></td>
        <td class="p-4 align-middle text-sm">${o.items.map(i => `${i.name} x${i.qty}`).join(', ')}</td>
        <td class="p-4 align-middle"><strong>$${o.total}</strong></td>
        <td class="p-4 align-middle"><span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${statusColors[o.status] || ''}">${o.status.replace('_', ' ')}</span></td>
        <td class="p-4 align-middle text-sm text-muted-foreground">${o.payment_method}</td>
      </tr>
    `).join('');
  } catch (e) { console.error(e); }
}

// ── Users ──
async function loadUsers() {
  try {
    const users = await API.getUsers();
    paginationState.users.data = users;
    renderUsersPage();
  } catch (e) { console.error(e); }
}

function renderUsersPage() {
  const tbody = document.getElementById('usersTableBody');
  if (!tbody) return;
  const page = getPageSlice('users');
  tbody.innerHTML = page.map(u => `
    <tr class="border-b transition-colors hover:bg-muted/50">
      <td class="p-4 align-middle font-medium">${escapeHtml(u.name)}</td>
      <td class="p-4 align-middle text-sm text-muted-foreground">${u.email}</td>
      <td class="p-4 align-middle"><span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${u.role === 'admin' ? 'text-destructive border-destructive/20 bg-destructive/10' : 'text-primary bg-primary/10 border-primary/20'}">${u.role}</span></td>
      <td class="p-4 align-middle text-sm">${getTeamLabel(u.expertise)}</td>
      <td class="p-4 align-middle"><span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold ${u.is_active ? 'text-green-700 bg-green-50 border-green-200' : 'text-muted-foreground bg-muted border-border'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
      <td class="p-4 align-middle">
        <button class="inline-flex items-center justify-center rounded-md text-xs font-medium transition-colors hover:bg-muted h-8 px-3 border" onclick="toggleUserActive('${u.id}', ${!u.is_active})">${u.is_active ? 'Deactivate' : 'Activate'}</button>
      </td>
    </tr>
  `).join('');
  renderPagination('usersPagination', 'users', 'renderUsersPage');
}

async function toggleUserActive(id, active) {
  try {
    await API.updateUser(id, { is_active: active });
    showToast(`User ${active ? 'activated' : 'deactivated'}`, 'success');
    loadUsers();
  } catch (e) { showToast('Failed', 'error'); }
}

function openCreateUserModal() { openModal('createUserModal'); }

async function createUser(e) {
  e.preventDefault();
  const team = document.getElementById('newUserTeam').value;
  const customExpertise = document.getElementById('newUserExpertise').value.trim();
  // If user entered custom expertise use it, otherwise use team keywords
  const expertise = customExpertise || TEAM_KEYWORDS[team] || '';

  try {
    await API.createUser({
      name: document.getElementById('newUserName').value,
      email: document.getElementById('newUserEmail').value,
      password: document.getElementById('newUserPassword').value,
      role: document.getElementById('newUserRole').value,
      expertise: expertise,
      description: document.getElementById('newUserDesc').value,
    });
    showToast('User created successfully!', 'success');
    closeModal('createUserModal');
    // Reset form
    document.getElementById('newUserName').value = '';
    document.getElementById('newUserEmail').value = '';
    document.getElementById('newUserPassword').value = '';
    document.getElementById('newUserExpertise').value = '';
    document.getElementById('newUserDesc').value = '';
    loadUsers();
  } catch (e) { showToast(e.message || 'Failed to create user', 'error'); }
}

// Auto-fill expertise when team changes
document.getElementById('newUserTeam')?.addEventListener('change', (e) => {
  const expertiseInput = document.getElementById('newUserExpertise');
  if (expertiseInput && !expertiseInput.value) {
    expertiseInput.value = TEAM_KEYWORDS[e.target.value] || '';
  }
});

async function uploadProducts(e) {
  e.preventDefault();
  const file = document.getElementById('productFile').files[0];
  if (!file) return;
  const btn = e.target.querySelector('button[type="submit"]');
  const orgBtnText = btn.innerHTML;
  btn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 mr-2 animate-spin"></i> Uploading...';
  btn.disabled = true;
  if(window.lucide) window.lucide.createIcons();
  
  const fd = new FormData(); fd.append('file', file);
  try {
    const res = await API.uploadProducts(fd);
    document.getElementById('productUploadResult').innerHTML = `<div class="p-3 bg-green-50 text-green-700 text-sm rounded-md border border-green-200 mt-4">${res.message}</div>`;
    showToast(res.message, 'success');
    loadProducts();
  } catch (e) { showToast(e.message || 'Upload failed', 'error'); }
  btn.innerHTML = orgBtnText;
  btn.disabled = false;
}

async function loadProducts() {
  try {
    const data = await API.get('/admin/products');
    paginationState.products.data = data;
    renderProductsPage();
  } catch (e) {
    console.error(e);
  }
}

function renderProductsPage() {
  const tbody = document.getElementById('productsTableBody');
  if (!tbody) return;
  const data = paginationState.products.data;
  if (!data.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted-foreground p-6">No products found. Upload CSV above.</td></tr>';
    return;
  }
  const page = getPageSlice('products');
  tbody.innerHTML = page.map(p => `
    <tr class="border-b transition-colors hover:bg-muted/50">
      <td class="p-4 align-middle font-medium">${p.name}</td>
      <td class="p-4 align-middle"><span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold">${p.category}</span></td>
      <td class="p-4 align-middle">$${p.price}</td>
      <td class="p-4 align-middle">${p.stock_count}</td>
      <td class="p-4 align-middle"><span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${p.is_available ? 'bg-primary/10 text-primary' : 'bg-destructive/10 text-destructive'}">${p.is_available ? 'In Stock' : 'Out'}</span></td>
      <td class="p-4 align-middle"><button class="inline-flex items-center justify-center rounded-md text-xs font-medium transition-colors hover:bg-destructive/10 text-destructive h-8 px-3 border border-destructive/20" onclick="deleteProduct('${p.id}')"><i data-lucide="trash-2" class="w-3 h-3 mr-1"></i>Delete</button></td>
    </tr>
  `).join('');
  if(window.lucide) window.lucide.createIcons();
  renderPagination('productsPagination', 'products', 'renderProductsPage');
}

async function deleteProduct(id) {
  if (!confirm('Delete this product?')) return;
  try {
    await API.delete(`/admin/products/${id}`);
    showToast('Product deleted', 'success');
    loadProducts();
  } catch (e) { showToast('Delete failed', 'error'); }
}

async function uploadDocument(e) {
  e.preventDefault();
  const file = document.getElementById('docFile').files[0];
  if (!file) return;
  const btn = e.target.querySelector('button[type="submit"]');
  const orgBtnText = btn.innerHTML;
  btn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 mr-2 animate-spin"></i> Indexing...';
  btn.disabled = true;
  if(window.lucide) window.lucide.createIcons();
  
  const fd = new FormData(); fd.append('file', file);
  try {
    const res = await API.uploadDocument(fd);
    document.getElementById('docUploadResult').innerHTML = `<div class="p-3 bg-green-50 text-green-700 text-sm rounded-md border border-green-200 mt-4">✅ ${res.message}</div>`;
    showToast(res.message, 'success');
    loadDocuments();
  } catch (e) { showToast(e.message || 'Upload failed', 'error'); }
  btn.innerHTML = orgBtnText;
  btn.disabled = false;
}

async function loadDocuments() {
  try {
    const data = await API.get('/admin/documents');
    paginationState.documents.data = data;
    renderDocumentsPage();
  } catch(e) { console.error(e); }
}

function renderDocumentsPage() {
  const tbody = document.getElementById('docsTableBody');
  if (!tbody) return;
  const data = paginationState.documents.data;
  if (!data.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted-foreground p-6">No documents found. Upload TXT/PDF.</td></tr>';
    return;
  }
  const page = getPageSlice('documents');
  tbody.innerHTML = page.map(d => `
    <tr class="border-b transition-colors hover:bg-muted/50">
      <td class="p-4 align-middle font-medium flex items-center gap-2">
        <i data-lucide="file-text" class="h-4 w-4 text-muted-foreground"></i>
        ${d.filename}
      </td>
      <td class="p-4 align-middle"><span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase bg-muted text-muted-foreground">${d.file_type}</span></td>
      <td class="p-4 align-middle">
        <span class="${d.chunk_count > 0 ? 'text-green-600 font-semibold' : 'text-destructive'}">${d.chunk_count || 0} Chunks</span>
        ${d.chunk_count > 0 ? ' ✅' : ' ⚠️'}
      </td>
      <td class="p-4 align-middle text-muted-foreground text-sm">${new Date(d.created_at).toLocaleDateString()}</td>
      <td class="p-4 align-middle"><button class="inline-flex items-center justify-center rounded-md text-xs font-medium transition-colors hover:bg-destructive/10 text-destructive h-8 px-3 border border-destructive/20" onclick="deleteDocument('${d.id}')"><i data-lucide="trash-2" class="w-3 h-3 mr-1"></i>Delete</button></td>
    </tr>
  `).join('');
  if(window.lucide) window.lucide.createIcons();
  renderPagination('docsPagination', 'documents', 'renderDocumentsPage');
}

async function deleteDocument(id) {
  if (!confirm('Delete this document and its RAG chunks?')) return;
  try {
    await API.delete(`/admin/documents/${id}`);
    showToast('Document deleted', 'success');
    loadDocuments();
  } catch (e) { showToast('Delete failed', 'error'); }
}

// ── Settings ──
async function loadSettings() {
  try {
    const s = await API.getSettings();
    document.getElementById('settingBotName').value = s.brand_name || 'niRvAG';
    document.getElementById('settingLogoUrl').value = s.logo_url || '';
    document.getElementById('settingWelcome').value = s.welcome_message || '';
    const toneEl = document.getElementById('settingTone');
    if (toneEl) toneEl.value = s.tone || 'professional';
    const colorEl = document.getElementById('settingColor');
    const colorTextEl = document.getElementById('settingColorText');
    if (colorEl) colorEl.value = s.color_primary || '#6366f1';
    if (colorTextEl) colorTextEl.value = s.color_primary || '#6366f1';
    updateSettingsPreview();
  } catch (e) { console.error(e); }
}

function updateSettingsPreview() {
  const name = document.getElementById('settingBotName')?.value || 'Bot';
  const welcome = document.getElementById('settingWelcome')?.value || 'Hello!';
  const avatarUrl = document.getElementById('settingLogoUrl')?.value;
  const previewBotName = document.getElementById('previewBotName');
  const previewWelcome = document.getElementById('previewWelcome');
  const previewAvatar = document.getElementById('previewAvatar');
  if (previewBotName) previewBotName.textContent = name;
  if (previewWelcome) previewWelcome.textContent = welcome;
  if (previewAvatar) {
    if (avatarUrl) {
      previewAvatar.innerHTML = `<img src="${avatarUrl}" alt="${name}">`;
    } else {
      previewAvatar.innerHTML = name[0].toUpperCase();
    }
  }
}

// Live preview updates
['settingBotName', 'settingWelcome', 'settingLogoUrl'].forEach(id => {
  document.getElementById(id)?.addEventListener('input', updateSettingsPreview);
});
document.getElementById('settingColor')?.addEventListener('input', (e) => {
  const colorTextEl = document.getElementById('settingColorText');
  if (colorTextEl) colorTextEl.value = e.target.value;
});
document.getElementById('settingColorText')?.addEventListener('input', (e) => {
  if (/^#[0-9a-f]{6}$/i.test(e.target.value)) {
    const colorEl = document.getElementById('settingColor');
    if (colorEl) colorEl.value = e.target.value;
  }
});

async function saveSettings(e) {
  e.preventDefault();
  try {
    await API.updateSettings({
      brand_name: document.getElementById('settingBotName').value,
      logo_url: document.getElementById('settingLogoUrl').value,
      welcome_message: document.getElementById('settingWelcome').value,
      tone: document.getElementById('settingTone')?.value || 'professional',
      color_primary: document.getElementById('settingColor')?.value || '#6366f1',
    });
    showToast('Settings saved!', 'success');
  } catch (e) { showToast('Failed to save', 'error'); }
}

// ── Utility ──
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ── Modal Helpers ──
function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

// ── Logout ──
function logout() { Auth.clear(); window.location.href = '/pages/login.html'; }
