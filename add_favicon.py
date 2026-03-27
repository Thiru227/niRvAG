import os

files_to_update = [
    'frontend/index.html',
    'frontend/pages/admin.html',
    'frontend/pages/attendee.html',
    'frontend/pages/chat.html',
    'frontend/pages/login.html',
]

favicon_tag = '<link rel="icon" type="image/svg+xml" href="/favicon.svg" />\n'

for path in files_to_update:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'favicon.svg' in content:
            continue
            
        content = content.replace('</head>', f'  {favicon_tag}</head>')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Added favicon to {path}")
