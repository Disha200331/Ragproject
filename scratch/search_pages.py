from llama_index.core import SimpleDirectoryReader
import re

print("Loading documents...")
reader = SimpleDirectoryReader(input_dir="data")
documents = reader.load_data()
print(f"Loaded {len(documents)} pages.")

keywords = ["consolidated RoA", "Net NPA", "Managing Director & CEO", "Amitabh Chaudhry", "Net Interest Margin", "NIM"]

for kw in keywords:
    print(f"\n=================== SEARCHING FOR: '{kw}' ===================")
    matches = []
    for idx, doc in enumerate(documents):
        text = doc.text
        # check case-insensitive match
        if kw.lower() in text.lower():
            matches.append(idx)
    
    print(f"Found keyword in {len(matches)} pages: {matches}")
    # print context of the first few matches
    for page_idx in matches[:3]:
        text = documents[page_idx].text
        # find matching position
        pos = text.lower().find(kw.lower())
        start = max(0, pos - 150)
        end = min(len(text), pos + len(kw) + 150)
        snippet = text[start:end].replace('\n', ' ')
        print(f"  - Page {page_idx + 1} (0-indexed {page_idx}): ... {snippet} ...")
