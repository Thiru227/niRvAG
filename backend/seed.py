"""
Run Supabase seed — cleans old data and seeds fresh
"""
import httpx
import bcrypt
import os
import csv
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv('SUPABASE_URL')
KEY = os.getenv('SUPABASE_SERVICE_KEY')
HEADERS = {
    'apikey': KEY,
    'Authorization': f'Bearer {KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}
REST = f"{URL}/rest/v1"

def api_delete(table, params=None):
    """Delete rows from table."""
    r = httpx.delete(f"{REST}/{table}", headers=HEADERS, params=params or {}, timeout=15)
    print(f"  DELETE {table}: {r.status_code}")
    return r

def api_insert(table, data):
    h = {**HEADERS, 'Prefer': 'return=representation,resolution=merge-duplicates'}
    r = httpx.post(f"{REST}/{table}", headers=h, json=data, timeout=15)
    print(f"  INSERT {table}: {r.status_code}")
    if r.status_code >= 400:
        print(f"  Error: {r.text[:200]}")
    return r

# Generate fresh bcrypt hashes
admin_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
agent_hash = bcrypt.hashpw(b'agent123', bcrypt.gensalt()).decode()

print("=" * 60)
print("NIRVAG — Fresh Database Seed")
print("=" * 60)
print(f"\nUsing Supabase URL: {URL}")

# ── Step 1: Clean old data ──
print("\n[1] Cleaning old data...")
api_delete('ticket_events', {'id': 'not.is.null'})
api_delete('tickets', {'id': 'not.is.null'})
api_delete('chat_sessions', {'id': 'not.is.null'})
api_delete('documents', {'id': 'not.is.null'})
api_delete('products', {'id': 'not.is.null'})
api_delete('chatbot_settings', {'id': 'not.is.null'})
api_delete('users', {'id': 'not.is.null'})

# ── Step 2: Seed users ──
print("\n[2] Seeding users...")
users = [
    {
        'name': 'Admin User',
        'email': 'admin@nirvag.com',
        'role': 'admin',
        'password_hash': admin_hash,
        'expertise': 'administration',
        'description': 'System administrator with full access to all platform features',
        'is_active': True
    },
    {
        'name': 'Ravi Kumar',
        'email': 'ravi@nirvag.com',
        'role': 'attendee',
        'password_hash': agent_hash,
        'expertise': 'order, shipping, delivery, tracking, dispatch, package, logistics',
        'description': 'Senior support agent specializing in order tracking, shipping issues, and delivery problems.',
        'is_active': True
    },
    {
        'name': 'Priya Sharma',
        'email': 'priya@nirvag.com',
        'role': 'attendee',
        'password_hash': agent_hash,
        'expertise': 'payment, refund, billing, invoice, transaction, EMI, wallet',
        'description': 'Billing specialist handling refund requests, payment disputes, and transaction issues.',
        'is_active': True
    },
    {
        'name': 'Amit Verma',
        'email': 'amit@nirvag.com',
        'role': 'attendee',
        'password_hash': agent_hash,
        'expertise': 'bug, error, technical, crash, login, password, account, app',
        'description': 'Technical support engineer resolving software bugs, login issues, and platform errors.',
        'is_active': True
    },
    {
        'name': 'Sneha Patel',
        'email': 'sneha@nirvag.com',
        'role': 'attendee',
        'password_hash': agent_hash,
        'expertise': 'product, feature, catalog, recommendation, warranty, return, exchange',
        'description': 'Product specialist providing recommendations, warranty details, and return guidance.',
        'is_active': True
    },
    {
        'name': 'Kiran Nair',
        'email': 'kiran@nirvag.com',
        'role': 'attendee',
        'password_hash': agent_hash,
        'expertise': 'general, support, help, feedback, complaint, escalation, info',
        'description': 'General support agent handling inquiries, feedback, and customer escalations.',
        'is_active': True
    }
]

for u in users:
    api_insert('users', u)

# ── Step 3: Seed chatbot settings ──
print("\n[3] Seeding chatbot settings...")
api_insert('chatbot_settings', {
    'brand_name': 'niRvAG',
    'tone': 'professional',
    'welcome_message': 'Hello! 👋 How can I help you today?',
    'color_primary': '#4F46E5'
})

# ── Step 4: Seed products from CSV ──
print("\n[4] Seeding products from CSV...")
csv_path = os.path.join(os.path.dirname(__file__), 'data', 'products.csv')
if os.path.exists(csv_path):
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            product = {
                'name': row['name'],
                'category': row['category'],
                'price': float(row['price']),
                'description': row['description'],
                'stock_count': int(row['stock_count']),
                'is_available': row['is_available'].lower() == 'true'
            }
            api_insert('products', product)
else:
    print("  WARNING: products.csv not found!")

print("\n" + "=" * 60)
print("DONE! Seeded 6 agents across 5 team categories:")
print("  🚚 Ravi Kumar — ravi@nirvag.com — Order & Shipping")
print("  💳 Priya Sharma — priya@nirvag.com — Billing & Payments")
print("  🔧 Amit Verma — amit@nirvag.com — Technical Support")
print("  📦 Sneha Patel — sneha@nirvag.com — Product Inquiries")
print("  💬 Kiran Nair — kiran@nirvag.com — General Support")
print("\nAll agent passwords: agent123")
print("Admin: admin@nirvag.com / admin123")
print("=" * 60)
