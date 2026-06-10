import os

file_path = r'C:\Users\User\.gemini\antigravity\brain\e9fc0b68-9b80-41d6-8a03-b71cd845ab82\.system_generated\steps\787\content.md'

if not os.path.exists(file_path):
    print("File does not exist")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

keywords = ['pe', 'p/e', 'forward', 'eps', 'earnings', 'price/earnings', 'ratio', 'valuation', 'multiple']

for i, line in enumerate(lines):
    line_lower = line.lower()
    # Skip JS block lines which are usually very long
    if len(line) > 1000:
        continue
    if any(keyword in line_lower for keyword in keywords):
        # Clean line for print
        clean_line = line.strip()
        if clean_line:
            print(f"Line {i+1}: {clean_line[:150]}")
