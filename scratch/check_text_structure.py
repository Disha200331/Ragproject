from llama_index.core import SimpleDirectoryReader
import re

reader = SimpleDirectoryReader(input_dir="data")
documents = reader.load_data()
text = documents[0].text

print(f"Total text length: {len(text)}")

# Find all blocks of text that don't have binary symbols and look like normal text
# We can search for paragraphs with at least 5 common English words (e.g., 'the', 'and', 'of', 'to', 'for')
paragraphs = text.split('\n')
print(f"Total lines: {len(paragraphs)}")

clean_lines = []
for idx, p in enumerate(paragraphs):
    words = re.findall(r'[a-zA-Z]+', p)
    common_words = [w for w in words if w.lower() in ['the', 'and', 'of', 'to', 'for', 'in', 'is', 'on', 'with', 'by', 'at']]
    if len(common_words) >= 3 and len(p) < 1000:
        clean_lines.append((idx, p))

print(f"Found {len(clean_lines)} lines resembling normal text.")
print("\nFirst 30 normal-looking lines:")
for idx, line in clean_lines[:30]:
    print(f"Line {idx}: {line.strip()}")
