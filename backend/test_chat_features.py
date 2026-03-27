"""Test chat features: order ownership, ticket context, session carryover"""
import requests

BASE = "http://127.0.0.1:5000/api"

print("="*60)
print("TEST 1: Order ownership — user asks about order NOT theirs")
print("="*60)
r = requests.post(f"{BASE}/chat", json={
    "message": "What is the status of order ORD-1235?",
    "user_name": "Test User",
    "user_email": "test@test.com"   # ORD-1235 belongs to anita@example.com
})
data = r.json()
print(f"Reply: {data['reply'][:200]}")
print(f"Session: {data['session_id']}")
sid = data['session_id']

print("\n" + "="*60)
print("TEST 2: Order ownership — user asks about their OWN order")
print("="*60)
r = requests.post(f"{BASE}/chat", json={
    "message": "What is the status of order ORD-1234?",
    "session_id": sid,
    "user_name": "Test User",
    "user_email": "test@test.com"   # ORD-1234 belongs to test@test.com
})
data = r.json()
print(f"Reply: {data['reply'][:200]}")

print("\n" + "="*60)
print("TEST 3: Context carryover — new session, same email")
print("="*60)
r = requests.post(f"{BASE}/chat", json={
    "message": "Can you remind me what we discussed earlier?",
    "user_name": "Test User",
    "user_email": "test@test.com"   # Should carry over context from test 1 & 2
})
data = r.json()
print(f"Reply: {data['reply'][:300]}")
print(f"New Session: {data['session_id']}")

print("\n" + "="*60)
print("TEST 4: Ticket status query")
print("="*60)
r = requests.post(f"{BASE}/chat", json={
    "message": "What is the status of my tickets?",
    "session_id": data['session_id'],
    "user_name": "Test User",
    "user_email": "test@test.com"
})
data = r.json()
print(f"Reply: {data['reply'][:300]}")

print("\n✅ All tests complete!")
