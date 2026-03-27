# 🎫 AI Ticketing + Customer Support Copilot
### Product Requirements Document + Build Prompt for Antigravity IDE
**Version:** 1.0  
**Stack:** React + Flask + Supabase + Render + Claude API  
**Deployment Target:** Render (Backend + Frontend)

---

## ⚡ TL;DR — What You're Building

A full-stack AI-powered customer support platform where:
- Users chat with an AI that understands intent + sentiment
- The AI auto-creates, prioritizes, and routes support tickets
- Attendants (agents) resolve tickets via text or voice
- Admins manage everything through a dedicated panel
- All state lives in Supabase; all AI reasoning uses Claude

---

## 🏗️ PART 1 — ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React SPA)                      │
│         Chat UI  │  Attendee Panel  │  Admin Dashboard       │
└────────────────────────┬────────────────────────────────────┘
                         │ REST / HTTP
┌────────────────────────▼────────────────────────────────────┐
│                  FLASK BACKEND (Render)                      │
│   /chat  /ticket  /upload  /login  /admin  /voice  /docs    │
└───────┬──────────────┬──────────────────────┬───────────────┘
        │              │                      │
┌───────▼──────┐ ┌─────▼──────┐   ┌──────────▼──────────┐
│  Claude API  │ │ ChromaDB   │   │     Supabase          │
│  (AI Layer)  │ │ (RAG/Docs) │   │  (Auth + DB + Store)  │
└──────────────┘ └────────────┘   └─────────────────────┘
        │
┌───────▼───────────────────────────┐
│  External Integrations            │
│  - SMTP (Email Notifications)     │
│  - ElevenLabs (Voice, optional)   │
│  - Whisper API (STT, optional)    │
└───────────────────────────────────┘
```

---

## 🗃️ PART 2 — SUPABASE DATABASE SCHEMA

> Use Supabase's SQL editor to run these migrations. Enable Row Level Security (RLS) on all tables.

### 2.1 Table: `users`
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'attendee', 'admin')),
  password_hash TEXT,                    -- NULL for customers (session-only)
  expertise TEXT,                        -- e.g. "payments", "shipping" (attendees only)
  description TEXT,                      -- attendee bio for smart routing
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.2 Table: `tickets`
```sql
CREATE TABLE tickets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_number SERIAL UNIQUE,           -- Human-readable: #1001, #1002
  user_name TEXT NOT NULL,
  user_email TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  priority TEXT NOT NULL DEFAULT 'medium'
    CHECK (priority IN ('low', 'medium', 'high', 'critical')),
  status TEXT NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'in_progress', 'escalated', 'closed')),
  sentiment TEXT DEFAULT 'neutral'
    CHECK (sentiment IN ('happy', 'neutral', 'frustrated', 'angry')),
  intent TEXT,                           -- e.g. "complaint", "inquiry", "refund_request"
  assigned_to UUID REFERENCES users(id),
  resolution_text TEXT,
  resolution_voice_url TEXT,             -- Supabase Storage URL
  escalation_reason TEXT,
  last_escalated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.3 Table: `chat_sessions`
```sql
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email TEXT NOT NULL,
  user_name TEXT NOT NULL,
  ticket_id UUID REFERENCES tickets(id),
  messages JSONB NOT NULL DEFAULT '[]',  -- [{role, content, timestamp}]
  summary TEXT,                          -- AI-generated summary for RAG
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.4 Table: `products`
```sql
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  price NUMERIC(10, 2) NOT NULL,
  description TEXT,
  stock_count INTEGER DEFAULT 0,
  is_available BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.5 Table: `documents`
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  filename TEXT NOT NULL,
  file_type TEXT NOT NULL,               -- 'pdf', 'txt'
  storage_path TEXT NOT NULL,            -- Supabase Storage path
  chunk_count INTEGER DEFAULT 0,
  indexed_at TIMESTAMPTZ,
  uploaded_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.6 Table: `ticket_events` (Audit Log)
```sql
CREATE TABLE ticket_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id UUID REFERENCES tickets(id) ON DELETE CASCADE,
  actor_email TEXT NOT NULL,
  event_type TEXT NOT NULL,
    -- 'created' | 'assigned' | 'status_change' | 'escalated' | 'resolved' | 'priority_change'
  old_value TEXT,
  new_value TEXT,
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.7 Table: `chatbot_settings`
```sql
CREATE TABLE chatbot_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tone TEXT DEFAULT 'professional',      -- professional | friendly | concise
  brand_name TEXT DEFAULT 'Support',
  welcome_message TEXT DEFAULT 'Hello! How can I help you today?',
  color_primary TEXT DEFAULT '#4F46E5',  -- hex
  logo_url TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.8 Supabase Storage Buckets
```
Buckets to create in Supabase Dashboard:
├── documents/      (PDFs, TXTs — private)
├── voice-notes/    (MP3/WAV resolutions — private)
└── brand-assets/   (logos — public)
```

---

## 🐍 PART 3 — FLASK BACKEND (Complete Spec)

### 3.1 Project Structure
```
backend/
├── app.py                    # Entry point, Flask app init
├── requirements.txt
├── .env                      # Secrets (never commit)
├── config.py                 # Config loader
├── routes/
│   ├── chat.py               # POST /chat
│   ├── tickets.py            # CRUD /ticket/*
│   ├── auth.py               # POST /login, /logout
│   ├── admin.py              # Admin-only routes
│   ├── attendee.py           # Attendee routes
│   ├── upload.py             # File upload routes
│   └── voice.py              # POST /voice/upload
├── services/
│   ├── ai_engine.py          # Claude API orchestrator
│   ├── rag.py                # ChromaDB + document retrieval
│   ├── routing.py            # Smart ticket assignment
│   ├── sentiment.py          # Sentiment + priority mapping
│   ├── email_service.py      # SMTP email sender
│   └── ocr.py                # PDF/OCR text extraction
├── models/
│   └── supabase_client.py    # Supabase Python client wrapper
└── utils/
    ├── auth_middleware.py     # JWT decorator
    └── validators.py
```

### 3.2 Environment Variables (`.env`)
```env
# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...         # Service role key (backend only)
SUPABASE_ANON_KEY=eyJ...

# Claude
ANTHROPIC_API_KEY=sk-ant-...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youremail@gmail.com
SMTP_PASS=yourapppassword
FROM_EMAIL=support@yourdomain.com

# Optional
ELEVENLABS_API_KEY=...
OPENAI_API_KEY=...                  # For Whisper STT

# App
SECRET_KEY=your-flask-secret
FLASK_ENV=production
CORS_ORIGIN=https://your-frontend.onrender.com
```

### 3.3 `requirements.txt`
```
flask==3.0.0
flask-cors==4.0.0
supabase==2.3.0
anthropic==0.21.0
chromadb==0.4.22
PyMuPDF==1.23.8
pdfplumber==0.10.3
pytesseract==0.3.10
sentence-transformers==2.3.1
python-dotenv==1.0.0
gunicorn==21.2.0
Pillow==10.2.0
python-multipart==0.0.7
```

---

## 🤖 PART 4 — AI ENGINE (Detailed Implementation)

### 4.1 Claude API Call — Core Chat
```python
# services/ai_engine.py

import anthropic
import json
from services.rag import retrieve_context
from models.supabase_client import get_products, get_chat_history

client = anthropic.Anthropic()

SYSTEM_PROMPT = """
You are a helpful customer support AI assistant for {brand_name}.
Your tone is: {tone}

You have access to:
- Company documentation (provided as context)
- Product catalog
- Order information

CRITICAL RULES:
1. Always respond in valid JSON with this EXACT structure:
{{
  "response": "Your reply to the customer (markdown allowed)",
  "intent": "one of: inquiry | complaint | refund_request | order_status | technical_issue | product_question | other",
  "sentiment": "one of: happy | neutral | frustrated | angry",
  "priority": "one of: low | medium | high | critical",
  "action": "one of: none | create_ticket | escalate | resolve",
  "ticket_title": "Short title if action is create_ticket, else null",
  "ticket_description": "Detailed description if create_ticket, else null"
}}

2. Set priority based on sentiment:
   - happy/neutral → low or medium
   - frustrated → medium or high  
   - angry → high or critical

3. Trigger create_ticket when:
   - User has a complaint or unresolved issue
   - Order/delivery problems are mentioned
   - User asks for a refund
   - Technical issues are reported

4. NEVER expose internal system details.
5. Be empathetic and solution-focused.

RAG CONTEXT:
{rag_context}

PRODUCT CATALOG SUMMARY:
{product_context}
"""

def process_chat(user_message: str, session_data: dict, chat_history: list) -> dict:
    brand_settings = get_brand_settings()
    
    # Retrieve RAG context
    rag_ctx = retrieve_context(user_message, top_k=3)
    
    # Get product context
    products = get_products(limit=20)
    product_summary = "\n".join([f"- {p['name']} ({p['category']}): ${p['price']}" for p in products])
    
    system = SYSTEM_PROMPT.format(
        brand_name=brand_settings.get('brand_name', 'Support'),
        tone=brand_settings.get('tone', 'professional'),
        rag_context=rag_ctx,
        product_context=product_summary
    )
    
    # Build messages array with history
    messages = []
    for msg in chat_history[-10:]:  # Last 10 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=system,
        messages=messages
    )
    
    raw = response.content[0].text
    
    # Safe JSON parse
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: extract JSON from response
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(match.group()) if match else {"response": raw, "action": "none", "sentiment": "neutral", "priority": "medium", "intent": "other"}
    
    return result
```

### 4.2 Routing Engine (LLM-Assisted)
```python
# services/routing.py

def assign_ticket_to_attendee(ticket_description: str, intent: str) -> dict | None:
    """Use Claude to find the best-fit attendee based on expertise + description."""
    
    attendees = get_active_attendees()
    if not attendees:
        return None
    
    attendee_list = "\n".join([
        f"- ID: {a['id']} | Name: {a['name']} | Expertise: {a['expertise']} | Bio: {a['description']}"
        for a in attendees
    ])
    
    prompt = f"""
    Given this support ticket:
    Intent: {intent}
    Description: {ticket_description}
    
    Available agents:
    {attendee_list}
    
    Return ONLY a JSON object:
    {{"assigned_id": "uuid-here", "reason": "brief reason"}}
    
    Pick the agent whose expertise and bio best matches the ticket issue.
    If no clear match, pick the one with most general expertise.
    """
    
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return json.loads(response.content[0].text)
```

---

## 📡 PART 5 — API ROUTES (Complete Specification)

### 5.1 Chat Route
```
POST /api/chat
Content-Type: application/json

Request:
{
  "message": "My order #123 hasn't arrived yet",
  "session_id": "uuid",          // null for new session
  "user_name": "Priya",
  "user_email": "priya@example.com"
}

Response:
{
  "reply": "I understand your frustration...",
  "session_id": "uuid",
  "ticket_created": true,
  "ticket": {
    "id": "uuid",
    "ticket_number": 1043,
    "status": "open",
    "priority": "high",
    "assigned_to": "Ravi"
  },
  "sentiment": "frustrated",
  "intent": "order_status"
}
```

### 5.2 Ticket Routes
```
GET    /api/tickets                     → List (admin/attendee filtered)
GET    /api/tickets/:id                 → Single ticket + events
POST   /api/tickets                     → Create (AI or manual)
PATCH  /api/tickets/:id                 → Update status/priority/assignment
POST   /api/tickets/:id/resolve         → Add resolution (text or voice)
POST   /api/tickets/:id/escalate        → Escalate with reason
GET    /api/tickets/:id/events          → Audit log
```

### 5.3 Auth Routes
```
POST /api/auth/login
Body: { email, password }
Response: { access_token, user: { id, name, role, expertise } }

POST /api/auth/logout
POST /api/auth/session          → Validate customer session (name+email only)
```

### 5.4 Admin Routes
```
POST   /api/admin/users             → Create attendee
GET    /api/admin/users             → List all users
PATCH  /api/admin/users/:id         → Update user
DELETE /api/admin/users/:id         → Deactivate

POST   /api/admin/settings          → Update chatbot settings
GET    /api/admin/settings          → Get settings

GET    /api/admin/analytics         → Dashboard metrics
```

### 5.5 Upload Routes
```
POST /api/upload/products
  Body: multipart/form-data, file: products.csv
  Action: Parse CSV → upsert to Supabase products table

POST /api/upload/document
  Body: multipart/form-data, file: faq.pdf
  Action: Extract text → chunk → embed → store in ChromaDB
          Record metadata in Supabase documents table
```

### 5.6 Voice Route
```
POST /api/voice/upload
  Body: multipart/form-data, audio: recording.webm, ticket_id: uuid
  Action:
    1. Transcribe via Whisper (or ElevenLabs)
    2. Upload audio to Supabase Storage (voice-notes/)
    3. Save resolution_text + resolution_voice_url to ticket
    4. Update ticket status → closed
    5. Trigger resolution email to customer
```

### 5.7 Analytics Route
```
GET /api/admin/analytics
Response:
{
  "total_tickets": 142,
  "open": 23,
  "in_progress": 18,
  "escalated": 5,
  "closed": 96,
  "avg_resolution_time_hours": 4.2,
  "sentiment_breakdown": {
    "happy": 30, "neutral": 60, "frustrated": 35, "angry": 17
  },
  "top_intents": [
    {"intent": "order_status", "count": 45},
    {"intent": "refund_request", "count": 28}
  ],
  "tickets_per_day": [{"date": "2025-01-01", "count": 12}, ...]
}
```

---

## 🎨 PART 6 — FRONTEND (React SPA)

### 6.1 Project Structure
```
frontend/
├── src/
│   ├── App.jsx
│   ├── main.jsx
│   ├── index.css
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatWidget.jsx         # Floating chat button
│   │   │   ├── ChatWindow.jsx         # Full chat UI
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── TicketConfirmation.jsx # Inline ticket creation card
│   │   │   └── UserEntryForm.jsx      # Name + email gate
│   │   ├── Admin/
│   │   │   ├── AdminLayout.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── TicketTable.jsx
│   │   │   ├── UserManagement.jsx
│   │   │   ├── ProductUpload.jsx
│   │   │   ├── DocumentUpload.jsx
│   │   │   └── ChatbotSettings.jsx
│   │   ├── Attendee/
│   │   │   ├── AttendeeLayout.jsx
│   │   │   ├── TicketQueue.jsx
│   │   │   ├── TicketDetail.jsx
│   │   │   ├── VoiceRecorder.jsx
│   │   │   └── ResolutionPanel.jsx
│   │   └── Shared/
│   │       ├── PriorityBadge.jsx
│   │       ├── SentimentIcon.jsx
│   │       ├── StatusPill.jsx
│   │       └── LoadingDots.jsx
│   ├── pages/
│   │   ├── Home.jsx                   # Chat interface
│   │   ├── Login.jsx
│   │   ├── AdminDashboard.jsx
│   │   └── AttendeeDashboard.jsx
│   ├── hooks/
│   │   ├── useChat.js
│   │   ├── useTickets.js
│   │   └── useAuth.js
│   ├── services/
│   │   └── api.js                     # Axios wrapper
│   └── store/
│       └── authStore.js               # Zustand store
├── public/
│   └── embed.js                       # Embeddable widget script
├── index.html
├── vite.config.js
└── package.json
```

### 6.2 Key UI Flows

#### Customer Chat Flow
```
1. User lands on page
2. ChatWidget (floating bubble) shown in corner
3. Click → UserEntryForm modal:
     [ Your Name: _________ ]
     [ Your Email: ________ ]
     [ Start Chat → ]
4. Session saved, ChatWindow opens
5. User types → streaming AI response
6. If ticket created → TicketConfirmation card appears:
     ┌─────────────────────────────┐
     │ ✅ Ticket Created            │
     │ ID: #1043                   │
     │ Assigned to: Ravi           │
     │ Priority: 🔴 High           │
     │ Status: Open                │
     └─────────────────────────────┘
```

#### Attendee Flow
```
1. Login → /attendee dashboard
2. See queue of assigned tickets sorted by priority
3. Click ticket → full detail view:
   - Chat history shown
   - Customer info
   - Current status + priority
4. Actions:
   - Change status (dropdown)
   - Change priority
   - Add text resolution
   - Record voice note → plays back → confirm → saves
   - Escalate (requires reason)
5. On resolve → email auto-sent to customer
```

#### Admin Flow
```
1. Login → /admin dashboard
2. Sidebar navigation:
   - 📊 Dashboard (metrics)
   - 🎫 All Tickets
   - 👥 User Management
   - 📦 Products
   - 📄 Documents
   - ⚙️ Settings
3. Can override any ticket field
4. Can create attendee accounts
5. Can upload product CSV + docs
6. Can customize chatbot tone, name, welcome message
```

---

## 📧 PART 7 — EMAIL NOTIFICATIONS

### 7.1 All Email Triggers

| Event | Recipient | Subject Template |
|-------|-----------|-----------------|
| Ticket created | Customer | `Your support ticket #{{number}} has been created` |
| Ticket assigned | Customer | `An agent has been assigned to your ticket #{{number}}` |
| Ticket escalated | Customer | `Your ticket #{{number}} has been escalated` |
| Ticket closed | Customer | `Your ticket #{{number}} has been resolved ✅` |
| New ticket assigned | Attendee | `New ticket assigned: #{{number}} — {{priority}} priority` |

### 7.2 Email Service Implementation
```python
# services/email_service.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TEMPLATES = {
    "ticket_created": {
        "subject": "Your support ticket #{number} has been created",
        "body": """
Hi {name},

We've received your support request and created ticket #{number}.

📋 Issue: {title}
🔴 Priority: {priority}
👤 Assigned to: {assigned_to}

Our team will get back to you shortly.

— {brand_name} Support Team
        """
    },
    "ticket_resolved": {
        "subject": "✅ Ticket #{number} has been resolved",
        "body": """
Hi {name},

Great news! Your support ticket #{number} has been resolved.

📋 Issue: {title}
✅ Resolution: {resolution}

If you have further questions, don't hesitate to reach out.

— {brand_name} Support Team
        """
    }
}

def send_email(to_email: str, template_key: str, variables: dict):
    template = TEMPLATES[template_key]
    subject = template["subject"].format(**variables)
    body = template["body"].format(**variables)
    # SMTP send logic...
```

---

## 🔁 PART 8 — ESCALATION RULES ENGINE

```python
# services/escalation.py

def check_auto_escalation(ticket: dict, new_message: str) -> dict:
    """
    Returns: { should_escalate: bool, reason: str }
    """
    
    # Rule 1: Angry sentiment on high-priority open ticket
    if ticket['sentiment'] == 'angry' and ticket['priority'] in ['high', 'critical']:
        return {"should_escalate": True, "reason": "Customer expressing anger on critical issue"}
    
    # Rule 2: Duplicate escalation protection (< 24 hours)
    if ticket.get('last_escalated_at'):
        from datetime import datetime, timezone, timedelta
        last_esc = datetime.fromisoformat(ticket['last_escalated_at'])
        if datetime.now(timezone.utc) - last_esc < timedelta(hours=24):
            return {"should_escalate": False, "reason": "Already escalated within 24 hours"}
    
    # Rule 3: Repeated complaint keyword detection
    complaint_keywords = ['still not resolved', 'again', 'same issue', 'third time', 'unacceptable']
    if any(kw in new_message.lower() for kw in complaint_keywords):
        return {"should_escalate": True, "reason": "Customer indicates repeated/unresolved issue"}
    
    return {"should_escalate": False, "reason": None}
```

---

## 📄 PART 9 — RAG SYSTEM (ChromaDB)

```python
# services/rag.py

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

chroma_client = chromadb.PersistentClient(path="./chroma_store")
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

collection = chroma_client.get_or_create_collection(
    name="support_docs",
    embedding_function=embedding_fn
)

def index_document(text: str, doc_id: str, filename: str):
    """Chunk → embed → store in ChromaDB"""
    
    chunks = chunk_text(text, chunk_size=400, overlap=50)
    
    collection.add(
        documents=chunks,
        ids=[f"{doc_id}_{i}" for i in range(len(chunks))],
        metadatas=[{"filename": filename, "chunk_index": i} for i in range(len(chunks))]
    )

def retrieve_context(query: str, top_k: int = 3) -> str:
    """Semantic search → return relevant context string"""
    
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    
    if not results['documents'][0]:
        return "No relevant documentation found."
    
    return "\n\n---\n".join(results['documents'][0])

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks
```

---

## 📦 PART 10 — OCR + DOCUMENT EXTRACTION

```python
# services/ocr.py

import fitz  # PyMuPDF
import pdfplumber

def extract_text_from_pdf(file_path: str) -> str:
    """
    Strategy:
    1. Try PyMuPDF first (fast, handles most PDFs)
    2. If text is sparse (< 100 chars/page avg), it's likely scanned
    3. Fallback to pytesseract for scanned docs
    """
    
    # Attempt 1: PyMuPDF
    doc = fitz.open(file_path)
    pages_text = [page.get_text() for page in doc]
    full_text = "\n".join(pages_text)
    
    avg_chars = len(full_text) / max(len(pages_text), 1)
    
    if avg_chars > 100:
        return full_text.strip()
    
    # Attempt 2: pdfplumber (better table/layout extraction)
    with pdfplumber.open(file_path) as pdf:
        text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        if len(text.strip()) > 200:
            return text.strip()
    
    # Attempt 3: OCR fallback (scanned PDF)
    import pytesseract
    from PIL import Image
    
    doc = fitz.open(file_path)
    ocr_text = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        ocr_text.append(pytesseract.image_to_string(img))
    
    return "\n".join(ocr_text).strip()
```

---

## 🚀 PART 11 — RENDER DEPLOYMENT

### 11.1 Backend — `render.yaml` (in `/backend`)
```yaml
services:
  - type: web
    name: ai-support-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: SMTP_HOST
        sync: false
      - key: SMTP_USER
        sync: false
      - key: SMTP_PASS
        sync: false
      - key: SECRET_KEY
        generateValue: true
    disk:
      name: chroma-store
      mountPath: /opt/render/project/src/chroma_store
      sizeGB: 1
```

### 11.2 Frontend — `render.yaml` (in `/frontend`)
```yaml
services:
  - type: web
    name: ai-support-frontend
    env: static
    buildCommand: npm install && npm run build
    staticPublishPath: ./dist
    envVars:
      - key: VITE_API_URL
        value: https://ai-support-backend.onrender.com
```

### 11.3 Deployment Checklist
```
Backend:
□ Set all env vars in Render dashboard
□ Enable persistent disk for ChromaDB
□ Add CORS origin pointing to frontend URL

Frontend:
□ Set VITE_API_URL env var
□ Add SPA redirect rule: /* → /index.html

Supabase:
□ Run all SQL migrations
□ Enable RLS on all tables
□ Create storage buckets: documents/, voice-notes/, brand-assets/
□ Create service role API key for backend
□ Enable email confirmation (or disable for dev)
```

---

## 🔐 PART 12 — AUTH + ROLE MIDDLEWARE

```python
# utils/auth_middleware.py

from functools import wraps
from flask import request, jsonify, g
import jwt

def require_auth(roles=None):
    """Decorator: validates JWT, optionally checks role"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                return jsonify({"error": "Unauthorized"}), 401
            
            try:
                payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                g.user = payload  # { id, email, role, name }
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401
            
            if roles and g.user.get('role') not in roles:
                return jsonify({"error": "Forbidden"}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# Usage:
# @require_auth(roles=['admin'])
# @require_auth(roles=['admin', 'attendee'])
# @require_auth()  # any authenticated user
```

---

## 📊 PART 13 — DASHBOARD METRICS QUERIES

```sql
-- Total ticket counts by status
SELECT status, COUNT(*) FROM tickets GROUP BY status;

-- Sentiment trend (last 30 days)
SELECT
  DATE_TRUNC('day', created_at) AS day,
  sentiment,
  COUNT(*) AS count
FROM tickets
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY day, sentiment
ORDER BY day;

-- Top intents
SELECT intent, COUNT(*) AS count
FROM tickets
GROUP BY intent
ORDER BY count DESC
LIMIT 10;

-- Avg resolution time
SELECT AVG(
  EXTRACT(EPOCH FROM (updated_at - created_at)) / 3600
) AS avg_hours
FROM tickets
WHERE status = 'closed';

-- Tickets per attendee
SELECT
  u.name,
  COUNT(t.id) AS total,
  SUM(CASE WHEN t.status = 'closed' THEN 1 ELSE 0 END) AS resolved
FROM tickets t
JOIN users u ON t.assigned_to = u.id
GROUP BY u.name;
```

---

## 🧩 PART 14 — EMBEDDABLE WIDGET

```javascript
// public/embed.js — Drop this on any website

(function() {
  const SUPPORT_URL = "https://your-frontend.onrender.com";
  
  // Create iframe container
  const container = document.createElement('div');
  container.id = 'ai-support-widget';
  container.style.cssText = `
    position: fixed; bottom: 24px; right: 24px;
    z-index: 99999; font-family: sans-serif;
  `;
  
  const iframe = document.createElement('iframe');
  iframe.src = `${SUPPORT_URL}?embedded=true`;
  iframe.style.cssText = `
    width: 400px; height: 600px; border: none;
    border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.2);
    display: none;
  `;
  
  const fab = document.createElement('button');
  fab.innerHTML = '💬';
  fab.style.cssText = `
    width: 56px; height: 56px; border-radius: 50%;
    background: #4F46E5; border: none; cursor: pointer;
    font-size: 24px; color: white;
    box-shadow: 0 4px 20px rgba(79,70,229,0.4);
  `;
  
  fab.onclick = () => {
    iframe.style.display = iframe.style.display === 'none' ? 'block' : 'none';
  };
  
  container.appendChild(iframe);
  container.appendChild(fab);
  document.body.appendChild(container);
})();

// Add to any site:
// <script src="https://your-frontend.onrender.com/embed.js"></script>
```

---

## ✅ PART 15 — COMPLETE BUILD CHECKLIST

### Phase 1 — Foundation
- [ ] Initialize Flask backend with CORS, .env loading
- [ ] Connect Supabase Python client
- [ ] Run all DB migrations in Supabase dashboard
- [ ] Create storage buckets
- [ ] Test Supabase read/write from Flask

### Phase 2 — AI Core
- [ ] Implement `ai_engine.py` with Claude
- [ ] Test JSON output parsing + fallback
- [ ] Implement ChromaDB setup + `rag.py`
- [ ] Test document indexing + retrieval
- [ ] Implement OCR pipeline

### Phase 3 — Ticket System
- [ ] CRUD routes for tickets
- [ ] Escalation rules engine
- [ ] Smart routing with LLM
- [ ] Ticket events audit log

### Phase 4 — Email + Voice
- [ ] SMTP email service + all templates
- [ ] Supabase Storage upload helpers
- [ ] Voice transcription (Whisper or ElevenLabs)
- [ ] Trigger email on all ticket events

### Phase 5 — Frontend
- [ ] Vite + React setup, TailwindCSS
- [ ] Zustand auth store
- [ ] UserEntryForm + ChatWindow + MessageBubble
- [ ] TicketConfirmation component
- [ ] Admin dashboard + all panels
- [ ] Attendee panel + VoiceRecorder
- [ ] Embeddable widget script

### Phase 6 — Deployment
- [ ] Backend deployed on Render (with persistent disk)
- [ ] Frontend deployed on Render (static site)
- [ ] All env vars set in Render dashboard
- [ ] End-to-end smoke test

---

## 🔑 SUMMARY — KEY DESIGN DECISIONS

| Decision | Choice | Reason |
|----------|--------|--------|
| Database | Supabase (Postgres) | Managed, real-time, auth built-in |
| Vector Store | ChromaDB (persistent) | Simple, self-hosted, no extra cost |
| AI Model | Claude Opus 4 | Best instruction-following for JSON output |
| Auth | JWT (Flask) + Supabase Auth | Flexible, session-free |
| File Storage | Supabase Storage | Integrated with DB, CDN-backed |
| Deployment | Render | Free tier, easy env management |
| Embeddings | sentence-transformers (local) | No API cost, fast inference |
| PDF Extraction | PyMuPDF → pdfplumber → Tesseract | Cascading fallback for all PDF types |

---

*Built with Claude + Supabase + Render — Production-ready AI customer support.*
