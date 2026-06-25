import os

if os.path.exists('projects.json') and os.path.getsize('projects.json') > 0:
    with open('projects.json', 'r') as f:
        print(f.read())