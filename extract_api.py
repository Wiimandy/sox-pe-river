with open('invesco_urllib.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re

matches = [m.start() for m in re.finditer('tabularListApiUrl', html)]
print(f"Matches: {len(matches)}")
for idx in matches:
    start = max(0, idx - 100)
    end = min(len(html), idx + 1500)  # print more characters after
    print(f"Match context:\n{html[start:end]}\n{'-'*50}")
