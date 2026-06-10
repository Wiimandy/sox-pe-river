import requests

url = 'https://www.invesco.com/us/en/financial-products/etfs/invesco-phlx-semiconductor-etf.html'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
}

try:
    print("Fetching page...")
    r = requests.get(url, headers=headers, timeout=20)
    print(f"Status Code: {r.status_code}")
    print(f"Response Length: {len(r.text)}")
    
    with open('invesco_page.html', 'w', encoding='utf-8') as f:
        f.write(r.text)
    print("Page written to invesco_page.html")
    
    # Search for keywords in the raw response
    keywords = ['35.53', 'forward p/e', 'pe ratio', 'price/earnings', 'earnings', 'characteristics', 'trailing']
    for kw in keywords:
        count = r.text.lower().count(kw)
        print(f"Keyword '{kw}': found {count} times")
except Exception as e:
    print(f"Error: {e}")
