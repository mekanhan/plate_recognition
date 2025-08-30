import json
import sys

data = json.load(sys.stdin)
for path, methods in data.get('paths', {}).items():
    for method in methods:
        if method != 'parameters':
            print(f'{method.upper():6} {path}')