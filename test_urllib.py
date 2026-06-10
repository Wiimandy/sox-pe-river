import urllib.request
import re

url = 'https://www.invesco.com/us/en/financial-products/etfs/invesco-phlx-semiconductor-etf.html'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})

try:
    print("Fetching page using urllib...")
    with urllib.request.urlopen(req, timeout=20) as response:
        html = response.read().decode('utf-8')
    print(f"Success! Length: {len(html)}")
    
    with open('invesco_urllib.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    # Search for metrics
    keywords = ['35.53', 'forward p/e', 'pe ratio', 'price/earnings', 'earnings', 'characteristics', 'trailing']
    for kw in keywords:
        count = html.lower().count(kw)
        print(f"Keyword '{kw}': found {count} times")
        
    # Let's search for any decimal number followed by 'x' or in tables
    # e.g., print all matches of Forward P/E if we can find them.
except Exception as e:
    print(f"Error: {e}")
