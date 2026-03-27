"""Quick verification of all features"""
import requests

BASE = "http://127.0.0.1:5000/api"

# Test 1: Order not theirs
r = requests.post(f"{BASE}/chat", json={"message": "Status of ORD-1235?", "user_name": "Test", "user_email": "test@test.com"}, timeout=20)
d = r.json()
print("TEST 1 (wrong order):", d["reply"][:120])
print()

# Test 2: Own order
r = requests.post(f"{BASE}/chat", json={"message": "Status of ORD-1234?", "user_name": "Test", "user_email": "test@test.com"}, timeout=20)
d = r.json()
print("TEST 2 (own order):", d["reply"][:120])
sid = d["session_id"]
print()

# Test 3: Ticket query
r = requests.post(f"{BASE}/chat", json={"message": "What are my tickets?", "user_name": "Test", "user_email": "test@test.com", "session_id": sid}, timeout=20)
d = r.json()
print("TEST 3 (tickets):", d["reply"][:150])
print()

# Test 4: Admin login
r = requests.post(f"{BASE}/auth/login", json={"email": "admin@nirvag.com", "password": "admin123"}, timeout=10)
print("TEST 4 (admin login):", r.status_code, "OK" if r.status_code == 200 else "FAIL")
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Test 5: Agent login
r = requests.post(f"{BASE}/auth/login", json={"email": "ravi@nirvag.com", "password": "agent123"}, timeout=10)
print("TEST 5 (agent login):", r.status_code, "OK" if r.status_code == 200 else "FAIL")

# Test 6: Products count
prods = requests.get(f"{BASE}/admin/products", headers=h).json()
print(f"TEST 6 (products): {len(prods)} products")

# Test 7: Docs + chunks
docs = requests.get(f"{BASE}/admin/documents", headers=h).json()
total_chunks = sum(d.get("chunk_count", 0) for d in docs)
print(f"TEST 7 (docs): {len(docs)} docs, {total_chunks} chunks")

# Test 8: Delete a product and verify
if prods:
    pid = prods[0]["id"]
    pname = prods[0]["name"]
    dr = requests.delete(f"{BASE}/admin/products/{pid}", headers=h)
    prods_after = requests.get(f"{BASE}/admin/products", headers=h).json()
    print(f"TEST 8 (delete): Deleted '{pname}' -> {len(prods)} -> {len(prods_after)}", "OK" if len(prods_after) < len(prods) else "FAIL")

print("\nALL TESTS DONE!")
