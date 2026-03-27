"""
Supabase REST Client — Direct httpx calls to PostgREST API
No heavy SDK dependencies required.
"""
import httpx
from config import Config

BASE_URL = Config.SUPABASE_URL
API_KEY = Config.SUPABASE_SERVICE_KEY
HEADERS = {
    'apikey': API_KEY,
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}
REST = f"{BASE_URL}/rest/v1"


def _get(table, params=None):
    r = httpx.get(f"{REST}/{table}", headers=HEADERS, params=params or {}, timeout=15)
    r.raise_for_status()
    return r.json()

def _post(table, data):
    r = httpx.post(f"{REST}/{table}", headers=HEADERS, json=data, timeout=15)
    r.raise_for_status()
    return r.json()

def _patch(table, data, match_params):
    """PATCH with query string filters (e.g. ?id=eq.xxx)"""
    r = httpx.patch(f"{REST}/{table}", headers=HEADERS, json=data, params=match_params, timeout=15)
    r.raise_for_status()
    return r.json()

def _upsert(table, data):
    h = {**HEADERS, 'Prefer': 'return=representation,resolution=merge-duplicates'}
    r = httpx.post(f"{REST}/{table}", headers=h, json=data, timeout=15)
    r.raise_for_status()
    return r.json()

def _delete(table, match_params):
    """DELETE with query string filters (e.g. ?id=eq.xxx)"""
    h = {**HEADERS, 'Prefer': 'return=representation'}
    r = httpx.delete(f"{REST}/{table}", headers=h, params=match_params, timeout=15)
    r.raise_for_status()
    if r.status_code == 204 or not r.text.strip():
        return []
    return r.json()


# ── User Helpers ──
def get_user_by_email(email: str):
    rows = _get('users', {'email': f'eq.{email}', 'select': '*', 'limit': '1'})
    return rows[0] if rows else None

def get_user_by_id(user_id: str):
    rows = _get('users', {'id': f'eq.{user_id}', 'select': '*', 'limit': '1'})
    return rows[0] if rows else None

def get_active_attendees():
    return _get('users', {'role': 'eq.attendee', 'is_active': 'eq.true', 'select': '*'})

def get_all_users():
    return _get('users', {
        'select': 'id,name,email,role,expertise,description,is_active,created_at',
        'order': 'created_at.desc'
    })

def create_user(data: dict):
    rows = _post('users', data)
    return rows[0] if rows else None

def update_user(user_id: str, data: dict):
    rows = _patch('users', data, {'id': f'eq.{user_id}'})
    return rows[0] if rows else None


# ── Product Helpers ──
def get_products(limit=20):
    return _get('products', {'is_available': 'eq.true', 'limit': str(limit), 'select': '*'})

def upsert_product(data: dict):
    return _upsert('products', data)


# ── Chat Session Helpers ──
def create_chat_session(user_email, user_name):
    rows = _post('chat_sessions', {
        'user_email': user_email,
        'user_name': user_name,
        'messages': []
    })
    return rows[0] if rows else None

def get_chat_session(session_id):
    rows = _get('chat_sessions', {'id': f'eq.{session_id}', 'select': '*', 'limit': '1'})
    if rows:
        row = rows[0]
        # Parse messages if stored as string
        if isinstance(row.get('messages'), str):
            import json
            try:
                row['messages'] = json.loads(row['messages'])
            except Exception:
                row['messages'] = []
        return row
    return None

def update_chat_messages(session_id, messages):
    _patch('chat_sessions', {'messages': messages}, {'id': f'eq.{session_id}'})

def get_chat_session_by_email(user_email):
    """Find the most recent chat session for a given email (for context carryover)."""
    rows = _get('chat_sessions', {
        'user_email': f'eq.{user_email}',
        'select': '*',
        'order': 'created_at.desc',
        'limit': '1'
    })
    if rows:
        row = rows[0]
        if isinstance(row.get('messages'), str):
            import json
            try:
                row['messages'] = json.loads(row['messages'])
            except Exception:
                row['messages'] = []
        return row
    return None

def get_tickets_by_email(user_email):
    """Get all tickets for a customer email."""
    return _get('tickets', {
        'user_email': f'eq.{user_email}',
        'select': '*',
        'order': 'created_at.desc'
    })


# ── Ticket Helpers ──
def create_ticket(data: dict):
    rows = _post('tickets', data)
    return rows[0] if rows else None

def get_tickets(filters: dict = None):
    params = {'select': '*', 'order': 'created_at.desc'}
    if filters:
        for key, value in filters.items():
            if value:
                params[key] = f'eq.{value}'
    return _get('tickets', params)

def get_ticket_by_id(ticket_id: str):
    rows = _get('tickets', {'id': f'eq.{ticket_id}', 'select': '*', 'limit': '1'})
    return rows[0] if rows else None

def update_ticket(ticket_id: str, data: dict):
    rows = _patch('tickets', data, {'id': f'eq.{ticket_id}'})
    return rows[0] if rows else None


# ── Ticket Events ──
def create_ticket_event(data: dict):
    _post('ticket_events', data)

def get_ticket_events(ticket_id: str):
    return _get('ticket_events', {
        'ticket_id': f'eq.{ticket_id}',
        'select': '*',
        'order': 'created_at.asc'
    })


# ── Chatbot Settings ──
def get_brand_settings():
    rows = _get('chatbot_settings', {'select': '*', 'limit': '1'})
    if rows:
        return rows[0]
    return {
        'brand_name': 'niRvAG',
        'tone': 'professional',
        'welcome_message': 'Hello! How can I help you today?',
        'color_primary': '#4F46E5',
        'logo_url': ''
    }

def update_brand_settings(data: dict):
    existing = _get('chatbot_settings', {'select': 'id', 'limit': '1'})
    if existing:
        _patch('chatbot_settings', data, {'id': f'eq.{existing[0]["id"]}'})
    else:
        _post('chatbot_settings', data)


# ── Documents ──
def create_document_record(data: dict):
    rows = _post('documents', data)
    return rows[0] if rows else None
