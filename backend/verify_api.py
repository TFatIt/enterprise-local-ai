import sys
import httpx
sys.stdout.reconfigure(encoding='utf-8')

client = httpx.Client(base_url='http://127.0.0.1:8000/api/v1')
login = client.post('/auth/login', json={'username_or_email': 'superadmin', 'password': 'Admin@123456'})
token = login.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print('=== VERIFYING API /departments ===')
depts = client.get('/departments', headers=headers).json()
for d in depts:
    print(f"ID={d['id']} | Code={d['code']} | Name={d['name']}")

print('=== VERIFYING API /documents ===')
docs = client.get('/documents', headers=headers).json()
print(f"Total documents: {len(docs)}")
for doc in docs:
    print(f"Doc: {doc['title']} | File: {doc['file_name']} | Dept: {doc['department_name']} | Size: {doc['file_size']} B | Chunks: {doc['total_chunks']}")
