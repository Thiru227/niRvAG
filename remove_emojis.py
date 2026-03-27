import os

files_to_update = [
    'frontend/js/admin.js',
    'frontend/js/api.js',
    'frontend/js/attendee.js',
    'frontend/pages/chat.html'
]

replacements = [
    ("const labels = { happy: '😊 Happy', neutral: '😐 Neutral', frustrated: '😤 Frustrated', angry: '😡 Angry' };",
     "const labels = { happy: 'Happy', neutral: 'Neutral', frustrated: 'Frustrated', angry: 'Angry' };"),
    ("const map = { happy: '😊', neutral: '😐', frustrated: '😤', angry: '😡' };",
     "const map = { happy: 'Happy', neutral: 'Neutral', frustrated: 'Frustrated', angry: 'Angry' };"),
    ("const sentimentEmoji = { happy: '😊', neutral: '😐', frustrated: '😤', angry: '😡' };",
     "const sentimentEmoji = { happy: 'Happy', neutral: 'Neutral', frustrated: 'Frustrated', angry: 'Angry' };"),
    ("const map = { low: '🟢', medium: '🟡', high: '🟠', critical: '🔴' };",
     "const map = { low: 'Low', medium: 'Medium', high: 'High', critical: 'Critical' };")
]

for path in files_to_update:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for old, new in replacements:
            content = content.replace(old, new)
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {path}")
