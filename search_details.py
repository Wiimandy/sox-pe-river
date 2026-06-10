import re

file_path = r'C:\Users\User\.gemini\antigravity\brain\e9fc0b68-9b80-41d6-8a03-b71cd845ab82\.system_generated\steps\787\content.md'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Total content length: {len(content)}")

# Let's search for "35.53"
matches = [m.start() for m in re.finditer('35\.53', content)]
print(f"Matches for '35.53': {len(matches)}")
for idx in matches:
    start = max(0, idx - 100)
    end = min(len(content), idx + 100)
    print(f"Context for 35.53:\n{content[start:end]}\n{'-'*40}")

# Let's search for "P/E" or "PE"
matches_pe = [m.start() for m in re.finditer('P/E|PE|Price/Earnings', content, re.IGNORECASE)]
print(f"Matches for P/E / PE / Price/Earnings: {len(matches_pe)}")
for idx in matches_pe[:20]:
    start = max(0, idx - 50)
    end = min(len(content), idx + 50)
    print(f"Context:\n{content[start:end]}\n{'-'*40}")
