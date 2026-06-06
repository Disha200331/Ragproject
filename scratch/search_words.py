from llama_index.core import SimpleDirectoryReader

reader = SimpleDirectoryReader(input_dir="data")
documents = reader.load_data()
text = documents[0].text

test_words = ["axis", "bank", "report", "consolidated", "director", "financial", "percent", "npa", "roa", "amitabh", "chaudhry"]
print("Word counts (case-insensitive):")
for w in test_words:
    count = text.lower().count(w)
    print(f"  - '{w}': {count}")

# Print first 2000 characters of the text
print("\n--- FIRST 2000 CHARACTERS OF EXTRACTED TEXT ---")
print(text[:2000])

# Print some random segment in the middle (e.g., around character 5,000,000)
print("\n--- MIDDLE 2000 CHARACTERS (around 5,000,000) ---")
print(text[5000000:5002000])
