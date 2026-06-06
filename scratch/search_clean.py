from llama_index.core import SimpleDirectoryReader
import re

reader = SimpleDirectoryReader(input_dir="data")
documents = reader.load_data()
text = documents[0].text

print(f"Total text length: {len(text)}")

# Clean text a bit and find normal English words
english_words = re.findall(r'[a-zA-Z]{3,}', text)
print(f"Total words found: {len(english_words)}")

# Find instances of 'Axis Bank' and check surrounding chars for binary data
pos = 0
matches = 0
while True:
    pos = text.lower().find("axis bank", pos)
    if pos == -1:
        break
    matches += 1
    start = max(0, pos - 100)
    end = min(len(text), pos + len("axis bank") + 100)
    snippet = text[start:end].encode('ascii', errors='ignore').decode('ascii')
    print(f"Match {matches}: {snippet}")
    pos += len("axis bank")
    if matches >= 10:
        break
