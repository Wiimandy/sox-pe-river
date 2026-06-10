with open('invesco_urllib.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re

keywords = ['price/earnings', 'characteristics', 'trailing']

for kw in keywords:
    print(f"\nMatches for keyword: {kw}")
    matches = [m.start() for m in re.finditer(kw, html, re.IGNORECASE)]
    for idx in matches:
        start = max(0, idx - 150)
        end = min(len(html), idx + 150)
        print(f"Context:\n{html[start:end]}\n{'-'*50}")
