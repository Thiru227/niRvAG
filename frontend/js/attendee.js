/* ============================================
   NIRVAG — Attendee Dashboard Logic
   ============================================ */

let currentTicketId = null;
let mediaRecorder = null;
let audioChunks = [];
let recordingTimer = null;
let recordingSeconds = 0;

document.addEventListener('DOMContentLoaded', () => {
  if (!Auth.requireAuth(['attendee'])) return;

  const user = Auth.getUser();
  if (user) {
    document.getElementById('sidebarUserNameA').textContent = user.name || 'Agent';
    document.getElementById('sidebarUserEmailA').textContent = user.email || '';
    document.getElementById('sidebarAvatarA').textContent = (user.name || 'A')[0].toUpperCase();
  }

  loadMyTickets();
});

/* ── Panel Nav ── */
function showPanel(panel) {
  document.querySelectorAll('.panel').forEach(p => p.classList.add('hidden'));
  document.getElementById(`panel-${panel}`).classList.remove('hidden');
  document.querySelectorAll('[data-panel]').forEach(l => {
    l.classList.remove('bg-muted', 'text-foreground');
    l.classList.add('text-muted-foreground');
  });
  const activeLink = document.querySelector(`[data-panel="${panel}"]`);
  if (activeLink) {
    activeLink.classList.remove('text-muted-foreground');
    activeLink.classList.add('bg-muted', 'text-foreground');
  }

  if (panel === 'queue') loadMyTickets();
  if (panel === 'resolved') loadResolvedTickets();
}

/* ── Load Tickets ── */
async function loadMyTickets() {
  try {
    const tickets = await API.getTickets('?mine=true&status=open,in_progress,escalated');
    document.getElementById('myTicketCount').textContent = tickets.length;
    renderTicketQueue(tickets, 'ticketQueueList');
  } catch (err) {
    document.getElementById('ticketQueueList').innerHTML = emptyTicketState('No tickets assigned to you yet.');
  }
}

async function loadResolvedTickets() {
  try {
    const tickets = await API.getTickets('?mine=true&status=closed');
    renderTicketQueue(tickets, 'resolvedTicketsList');
  } catch (err) {
    document.getElementById('resolvedTicketsList').innerHTML = emptyTicketState('No resolved tickets.');
  }
}

function emptyTicketState(msg) {
  return `
    <div class="flex flex-col items-center justify-center p-12 text-center rounded-xl border bg-card text-muted-foreground shadow-sm">
      <i data-lucide="inbox" class="w-12 h-12 mb-4 text-muted-foreground/50"></i>
      <h3 class="text-lg font-semibold text-foreground mb-1">${msg}</h3>
      <p class="text-sm">Tickets will appear here when assigned to you by the AI routing engine.</p>
    </div>
  `;
}

/** Render ticket cards */
function renderTicketQueue(tickets, containerId) {
  const container = document.getElementById(containerId);

  if (!tickets || tickets.length === 0) {
    container.innerHTML = emptyTicketState('No tickets found');
    return;
  }

  // Sort: critical > high > medium > low
  const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  tickets.sort((a, b) => (priorityOrder[a.priority] || 3) - (priorityOrder[b.priority] || 3));

  container.innerHTML = tickets.map(t => `
    <div class="rounded-xl border bg-card text-card-foreground shadow-sm p-4 hover:shadow-md transition-shadow cursor-pointer flex items-center gap-4 group" onclick="openTicketDetail('${t.id}')">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-2">
          <span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold text-muted-foreground bg-muted">#${t.ticket_number || '—'}</span>
          <span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold tracking-wide uppercase ${t.priority==='critical'?'text-destructive border-destructive/20 bg-destructive/10' : t.priority==='high' ? 'text-yellow-600 bg-yellow-50 border-yellow-200' : 'text-primary bg-primary/10 border-primary/20'}">${t.priority}</span>
          <span class="inline-flex items-center text-[10px] uppercase font-semibold text-muted-foreground bg-accent px-2.5 py-0.5 rounded-sm">${t.status.replace('_', ' ')}</span>
        </div>
        <h4 class="text-sm font-semibold mb-1 truncate">${escapeHtmlAtt(t.title)}</h4>
        <div class="text-xs text-muted-foreground flex items-center gap-1.5">
          <i data-lucide="user" class="w-3 h-3"></i> ${escapeHtmlAtt(t.user_name)} 
          <span class="opacity-50">•</span> 
          ${getSentimentEmoji(t.sentiment)} ${capitalize(t.sentiment || 'neutral')} 
          <span class="opacity-50">•</span> 
          <i data-lucide="clock" class="w-3 h-3"></i> ${formatRelative(t.created_at)}
        </div>
      </div>
      <i data-lucide="chevron-right" class="w-5 h-5 text-muted-foreground group-hover:text-foreground transition-colors mr-2"></i>
    </div>
  `).join('');
  if(window.lucide) window.lucide.createIcons();
}

/* ── Ticket Detail ── */
async function openTicketDetail(id) {
  currentTicketId = id;
  try {
    const ticket = await API.getTicket(id);
    const events = await API.getTicketEvents(id);

    const content = document.getElementById('attTicketContent');
    content.innerHTML = `
      <div class="space-y-6">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold text-muted-foreground bg-muted">#${ticket.ticket_number || ''}</span>
          <span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold tracking-wide uppercase ${ticket.priority==='critical'?'text-destructive border-destructive/20 bg-destructive/10' : ticket.priority==='high' ? 'text-yellow-600 bg-yellow-50 border-yellow-200' : 'text-primary bg-primary/10 border-primary/20'}">${ticket.priority}</span>
          <span class="inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors">${capitalize(ticket.status.replace('_',' '))}</span>
          <span class="text-sm bg-accent rounded-full px-2 py-0.5 flex items-center">${getSentimentEmoji(ticket.sentiment)}</span>
        </div>
        <h2 class="text-xl font-bold">${escapeHtmlAtt(ticket.title)}</h2>
        
        <div class="bg-muted/50 rounded-lg p-4 border">
          <div class="text-xs text-muted-foreground mb-2 flex items-center gap-1"><i data-lucide="user" class="w-3 h-3"></i> Customer: <span class="font-medium text-foreground">${escapeHtmlAtt(ticket.user_name)}</span> (${escapeHtmlAtt(ticket.user_email)})</div>
          <p class="text-sm text-foreground leading-relaxed">${escapeHtmlAtt(ticket.description)}</p>
        </div>

        <!-- Actions -->
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <label class="text-sm font-medium leading-none">Status</label>
            <select id="attStatusSelect" onchange="updateAttTicketField('status', this.value)" class="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
              <option value="open" ${ticket.status === 'open' ? 'selected' : ''}>Open</option>
              <option value="in_progress" ${ticket.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
              <option value="escalated" ${ticket.status === 'escalated' ? 'selected' : ''}>Escalated</option>
              <option value="closed" ${ticket.status === 'closed' ? 'selected' : ''}>Closed</option>
            </select>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium leading-none">Priority</label>
            <select id="attPrioritySelect" onchange="updateAttTicketField('priority', this.value)" class="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
              <option value="low" ${ticket.priority === 'low' ? 'selected' : ''}>Low</option>
              <option value="medium" ${ticket.priority === 'medium' ? 'selected' : ''}>Medium</option>
              <option value="high" ${ticket.priority === 'high' ? 'selected' : ''}>High</option>
              <option value="critical" ${ticket.priority === 'critical' ? 'selected' : ''}>Critical</option>
            </select>
          </div>
        </div>

        <!-- Resolution -->
        <div class="space-y-2">
          <label class="text-sm font-medium leading-none">Resolution Note</label>
          <textarea id="attResolutionText" rows="3" class="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" placeholder="Describe how you resolved this issue...">${ticket.resolution_text || ''}</textarea>
        </div>
        <div class="flex gap-3">
          <button class="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4" onclick="resolveTicket()">
            <i data-lucide="check-circle" class="w-4 h-4 mr-2"></i> Resolve & Close
          </button>
          <button class="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-destructive bg-transparent text-destructive hover:bg-destructive/10 h-10 px-4" onclick="escalateTicketAtt()">
            <i data-lucide="alert-triangle" class="w-4 h-4 mr-2"></i> Escalate
          </button>
        </div>

        <!-- Voice Recorder -->
        <div class="flex items-center gap-4 p-4 border rounded-lg bg-card shadow-sm mt-4">
          <button class="w-10 h-10 flex border items-center justify-center rounded-full transition-all focus:outline-none recording-pulse" id="voiceRecordBtn" onclick="toggleRecording()">
            <i data-lucide="mic" class="w-4 h-4"></i>
          </button>
          <div class="flex flex-col">
            <span class="text-sm font-semibold" id="voiceStatus">Voice Resolution Note</span>
            <span class="text-xs text-muted-foreground" id="voiceTimer">Click mic to record a spoken resolution</span>
          </div>
        </div>

        <!-- Timeline -->
        ${events && events.length > 0 ? `
          <div class="mt-8 pt-6 border-t">
            <h4 class="text-sm font-semibold mb-4">Ticket Activity</h4>
            <div class="space-y-4">
              ${events.map(ev => `
                <div class="flex gap-4">
                  <div class="mt-1 flex-shrink-0 w-2 h-2 rounded-full bg-primary/40 ring-4 ring-primary/10"></div>
                  <div class="flex flex-col">
                    <span class="text-sm font-medium">${capitalize(ev.event_type)} <span class="font-normal text-muted-foreground">${ev.new_value ? ` → ${ev.new_value}` : ''}</span></span>
                    ${ev.note ? `<span class="text-sm text-foreground my-1">${ev.note}</span>` : ''}
                    <span class="text-xs text-muted-foreground">${formatRelative(ev.created_at)}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;

    document.getElementById('attTicketTitle').innerHTML = `Ticket <span class="opacity-50 font-normal">#${ticket.ticket_number || ''}</span>`;
    document.getElementById('attendeeTicketModal').classList.remove('hidden');
    if(window.lucide) window.lucide.createIcons();
  } catch (err) {
    showToast('Failed to load ticket', 'error');
  }
}

async function updateAttTicketField(field, value) {
  if (!currentTicketId) return;
  try {
    await API.updateTicket(currentTicketId, { [field]: value });
    showToast(`${capitalize(field)} updated`, 'success');
  } catch (err) {
    showToast('Update failed', 'error');
  }
}

async function resolveTicket() {
  if (!currentTicketId) return;
  const text = document.getElementById('attResolutionText').value.trim();
  if (!text) {
    showToast('Please enter a resolution note', 'warning');
    return;
  }
  try {
    await API.resolveTicket(currentTicketId, { resolution_text: text });
    showToast('Ticket resolved! Customer will be notified.', 'success');
    closeAttModal();
    loadMyTickets();
  } catch (err) {
    showToast('Failed to resolve', 'error');
  }
}

async function escalateTicketAtt() {
  const reason = prompt('Enter escalation reason:');
  if (!reason) return;
  try {
    await API.escalateTicket(currentTicketId, reason);
    showToast('Ticket escalated', 'success');
    closeAttModal();
    loadMyTickets();
  } catch (err) {
    showToast('Failed to escalate', 'error');
  }
}

/* ── Voice Recording ── */
function toggleRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    stopRecording();
  } else {
    startRecording();
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    recordingSeconds = 0;

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = uploadVoiceNote;

    mediaRecorder.start();
    
    const btn = document.getElementById('voiceRecordBtn');
    btn.classList.add('bg-destructive', 'text-destructive-foreground', 'border-destructive');
    btn.innerHTML = '<i data-lucide="square" class="w-4 h-4 fill-current"></i>';
    if(window.lucide) window.lucide.createIcons();
    document.getElementById('voiceStatus').textContent = 'Recording...';

    recordingTimer = setInterval(() => {
      recordingSeconds++;
      const min = Math.floor(recordingSeconds / 60).toString().padStart(2, '0');
      const sec = (recordingSeconds % 60).toString().padStart(2, '0');
      document.getElementById('voiceTimer').textContent = `${min}:${sec}`;
    }, 1000);
  } catch (err) {
    showToast('Microphone access denied', 'error');
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
    clearInterval(recordingTimer);

    const btn = document.getElementById('voiceRecordBtn');
    btn.classList.remove('bg-destructive', 'text-destructive-foreground', 'border-destructive');
    btn.innerHTML = '<i data-lucide="mic" class="w-4 h-4"></i>';
    if(window.lucide) window.lucide.createIcons();
    document.getElementById('voiceStatus').textContent = 'Uploading...';
  }
}

async function uploadVoiceNote() {
  const blob = new Blob(audioChunks, { type: 'audio/webm' });
  const formData = new FormData();
  formData.append('audio', blob, 'recording.webm');
  formData.append('ticket_id', currentTicketId);

  try {
    await API.uploadVoice(formData);
    showToast('Voice note uploaded & ticket resolved!', 'success');
    document.getElementById('voiceStatus').textContent = 'Uploaded ✅';
    document.getElementById('voiceTimer').textContent = 'Voice note saved';
    closeAttModal();
    loadMyTickets();
  } catch (err) {
    document.getElementById('voiceStatus').textContent = 'Upload failed';
    showToast('Voice upload failed', 'error');
  }
}

function closeAttModal() {
  document.getElementById('attendeeTicketModal').classList.add('hidden');
  currentTicketId = null;
}

function handleLogoutAttendee() {
  Auth.clear();
  window.location.href = 'login.html';
}

function escapeHtmlAtt(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
