"""
Ultra-Simple RAG - Direct Query
Just load docs and query without building indexes
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import time

load_dotenv()

print("=" * 70)
print("ULTRA-SIMPLE RAG - DIRECT QUERY")
print("=" * 70)

# Step 1: Load documents
print("\n[1] Loading documents...")
try:
    from llama_index.core import SimpleDirectoryReader
    pdf_dir = Path("data")
    documents = SimpleDirectoryReader(str(pdf_dir)).load_data()
    print(f"✅ Loaded {len(documents)} document(s)")
    print(f"   Total characters: {sum(len(doc.get_content()) for doc in documents)}")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Step 2: Initialize LLM
print("\n[2] Initializing LLM...")
try:
    from llama_index.llms.ollama import Ollama
    llm = Ollama(model="gemma3:1b", request_timeout=300.0, temperature=0.1)
    print("✅ Ollama ready")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Step 3: Direct query
print("\n[3] Querying document content directly...\n")
try:
    # Combine all document text
    full_text = "\n\n".join([doc.get_content() for doc in documents])
    
    print("Question: What was Axis Bank's consolidated RoA and Net NPA?")
    print("(Querying LLM - this may take 1-2 minutes...)\n")
    
    response = llm.complete(
        f"""Based on the following document, answer this question:
        
Question: What was Axis Bank's consolidated RoA and Net NPA?

Document:
{full_text[:5000]}  # Use first 5000 chars to avoid token limit

Answer:"""
    )
    
    print(f"Answer:\n{response}\n")
    print("✅ Query successful!")
    
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ DIRECT QUERY WORKING!")
print("=" * 70)
print("\nNote: This is a simple direct query.")
print("For better results with large documents, you can:")
print("1. Add delays between steps")
print("2. Use a simpler embedding model")
print("3. Process documents in smaller chunks")
