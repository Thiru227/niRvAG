import os

REPLACEMENTS = {
    "niRvAG": "niRvAG",
    "nirvag": "nirvag",  # for emails and css classes
    "NIRVAG": "NIRVAG",
}

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return
        
    original = content
    for old, new in REPLACEMENTS.items():
        content = content.replace(old, new)
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, _, files in os.walk('.'):
    if '.git' in root or '.venv' in root or '__pycache__' in root or 'node_modules' in root or 'chroma_store' in root:
        continue
    for file in files:
        if file.endswith(('.html', '.js', '.css', '.py', '.json', '.md', '.txt', '.env')):
            process_file(os.path.join(root, file))
