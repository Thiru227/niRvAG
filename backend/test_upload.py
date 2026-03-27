"""Upload rich content documents via API for RAG indexing."""
import requests
import json

BASE = "http://127.0.0.1:5000/api"

# Login as admin
r = requests.post(f"{BASE}/auth/login", json={"email": "admin@nirvag.com", "password": "admin123"})
if r.status_code != 200:
    print(f"Login failed: {r.text}")
    exit(1)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✅ Logged in as admin")

# Upload company_info.txt
print("\n[1] Uploading company_info.txt...")
with open("data/company_info.txt", "rb") as f:
    r = requests.post(f"{BASE}/upload/document", headers=headers, files={"file": ("company_info.txt", f, "text/plain")}, timeout=120)
print(f"  Status: {r.status_code} — {r.json().get('message', r.text[:100])}")

# Upload faq.txt
print("\n[2] Uploading faq.txt...")
with open("data/faq.txt", "rb") as f:
    r = requests.post(f"{BASE}/upload/document", headers=headers, files={"file": ("faq.txt", f, "text/plain")}, timeout=120)
print(f"  Status: {r.status_code} — {r.json().get('message', r.text[:100])}")

# Upload products CSV
print("\n[3] Uploading products.csv...")
with open("data/products.csv", "rb") as f:
    r = requests.post(f"{BASE}/upload/products", headers=headers, files={"file": ("products.csv", f, "text/csv")}, timeout=120)
print(f"  Status: {r.status_code} — {r.json().get('message', r.text[:100])}")

# Test chat
print("\n[4] Testing chat...")
r = requests.post(f"{BASE}/chat", json={"message": "What is your return policy?", "user_name": "Test", "user_email": "test@test.com"}, timeout=60)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"  Reply: {d.get('reply', '')[:200]}")
    print(f"  Ticket: {d.get('ticket_created')}")

# Test login as agent
print("\n[5] Testing agent login (ravi@nirvag.com / agent123)...")
r = requests.post(f"{BASE}/auth/login", json={"email": "ravi@nirvag.com", "password": "agent123"})
print(f"  Status: {r.status_code} — {r.json().get('user', {}).get('name', r.text[:100])}")

print("\n[6] Testing agent login (priya@nirvag.com / agent123)...")
r = requests.post(f"{BASE}/auth/login", json={"email": "priya@nirvag.com", "password": "agent123"})
print(f"  Status: {r.status_code} — {r.json().get('user', {}).get('name', r.text[:100])}")

print("\n✅ All tests complete!")
