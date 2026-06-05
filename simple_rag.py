"""
Simple RAG Pipeline - No Complex Knowledge Graph
Just load docs, embed them, and query
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("SIMPLE RAG PIPELINE - STEP BY STEP")
print("=" * 70)

# Step 1: Load documents
print("\n[Step 1] Loading documents...")
try:
    from llama_index.core import SimpleDirectoryReader
    pdf_dir = Path("data")
    documents = SimpleDirectoryReader(str(pdf_dir)).load_data()
    print(f"✅ Loaded {len(documents)} document(s)")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Step 2: Initialize LLM
print("\n[Step 2] Initializing Ollama LLM...")
try:
    from llama_index.llms.ollama import Ollama
    llm = Ollama(model="gemma3:1b", request_timeout=300.0, temperature=0.1)
    print("✅ Ollama initialized")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Step 3: Initialize Embeddings
print("\n[Step 3] Loading embeddings model...")
try:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core import Settings
    
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 512
    print("✅ Embeddings loaded")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Step 4: Create simple vector index
print("\n[Step 4] Creating vector index...")
try:
    from llama_index.core import VectorStoreIndex
    index = VectorStoreIndex.from_documents(documents, show_progress=True)
    print("✅ Vector index created")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Step 5: Create query engine
print("\n[Step 5] Creating query engine...")
try:
    query_engine = index.as_query_engine(similarity_top_k=5, llm=llm)
    print("✅ Query engine ready")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Step 6: Test queries
print("\n[Step 6] Testing queries...\n")
try:
    print("Query 1: What was Axis Bank's consolidated RoA and Net NPA for fiscal 2025?")
    response = query_engine.query("What was Axis Bank's consolidated RoA and Net NPA for fiscal 2025?")
    print(f"Answer: {response}\n")
    
    print("Query 2: Who is the Managing Director & CEO of Axis Bank?")
    response = query_engine.query("Who is the Managing Director & CEO of Axis Bank?")
    print(f"Answer: {response}\n")
    
    print("✅ Pipeline working!")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

print("=" * 70)
print("✅ SIMPLE RAG PIPELINE COMPLETED!")
print("=" * 70)
