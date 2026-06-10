import urllib.request
import json

url = 'https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/46138G615?expand=nav&idType=cusip&variationType=fundCharacteristics&productType=ETF'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})

try:
    print(f"Requesting Invesco API: {url}")
    with urllib.request.urlopen(req, timeout=15) as response:
        res_data = response.read().decode('utf-8')
    print("Success! Parsing JSON...")
    data = json.loads(res_data)
    print(json.dumps(data, indent=2)[:2000]) # Print first 2000 chars of output
except Exception as e:
    print(f"Error calling API: {e}")
