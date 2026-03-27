"""Test delete endpoints"""
import requests

BASE = "http://127.0.0.1:5000/api"

# Login
r = requests.post(f"{BASE}/auth/login", json={"email": "admin@nirvag.com", "password": "admin123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test product delete
prods = requests.get(f"{BASE}/admin/products", headers=headers).json()
print(f"Products before: {len(prods)}")
if prods:
    pid = prods[0]["id"]
    pname = prods[0]["name"]
    print(f"Deleting product: {pname} ({pid})")
    dr = requests.delete(f"{BASE}/admin/products/{pid}", headers=headers)
    print(f"  Status: {dr.status_code}")
    print(f"  Body: {dr.text[:200]}")
    
    prods2 = requests.get(f"{BASE}/admin/products", headers=headers).json()
    print(f"Products after: {len(prods2)}")

# Test document delete
docs = requests.get(f"{BASE}/admin/documents", headers=headers).json()
print(f"\nDocuments before: {len(docs)}")
if docs:
    did = docs[0]["id"]
    dname = docs[0]["filename"]
    print(f"Deleting doc: {dname} ({did})")
    dr = requests.delete(f"{BASE}/admin/documents/{did}", headers=headers)
    print(f"  Status: {dr.status_code}")
    print(f"  Body: {dr.text[:200]}")
    
    docs2 = requests.get(f"{BASE}/admin/documents", headers=headers).json()
    print(f"Documents after: {len(docs2)}")
