from llama_index.core import SimpleDirectoryReader
import os

reader = SimpleDirectoryReader(input_dir="data")
print("Supported file extractors in SimpleDirectoryReader:")
for ext, ext_reader in reader.file_extractor.items():
    print(f"  - {ext}: {ext_reader.__class__.__name__}")
