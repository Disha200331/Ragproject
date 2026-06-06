#!/usr/bin/env python3
"""
RAG Pipeline - FAST MODE (for CPU-bound systems)
Uses tinyllama for faster processing (trades accuracy for speed)
Processes fewer relationships per chunk for faster execution
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import requests
import time
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment variables
load_dotenv()

logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger(__name__)

# Async compatibility
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

print("[1/6] Importing LlamaIndex modules...")
from llama_index.core import SimpleDirectoryReader, Settings, PropertyGraphIndex
from llama_index.core.indices.property_graph import SimpleLLMPathExtractor
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

print("=" * 70)
print("  RAG PIPELINE - FAST MODE (TinyLLaMA)")
print("  Running at:", time.strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 70)

# =====================================================================
# 1. Initialize Models (TinyLLaMA - Much Faster!)
# =====================================================================
try:
    print("\n[2/6] Initializing Models (FAST MODE)...")
    print("   Checking Ollama connection (timeout: 10s)...")

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            print(f"   ✓ Ollama running with {len(models)} model(s)")
            
            # Check for tinyllama
            has_tinyllama = any("tinyllama" in n.lower() for n in model_names)
            if not has_tinyllama:
                print(f"   ⚠ tinyllama not found - using gemma3:1b")
                model_to_use = "gemma3:1b"
            else:
                print(f"   ✓ tinyllama:latest found (much faster!)")
                model_to_use = "tinyllama:latest"
        else:
            raise Exception(f"Ollama returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Ollama is not running: {e}")
        sys.exit(1)

    # Initialize LLM with SHORTER timeout for fast mode
    llm = Ollama(
        model=model_to_use,
        request_timeout=300.0,  # 5 minutes (tinyllama is faster)
        temperature=0.1,
        context_window=2048,    # Reduced from 4096
    )
    print(f"   ✓ Ollama LLM ({model_to_use}) initialized")

    print("   Loading BGE embeddings...")
    embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-large-en-v1.5",
        max_length=512
    )
    print("   ✓ BGE embeddings loaded")

    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 256  # Reduced from 512 (smaller chunks = faster)
    Settings.chunk_overlap = 20  # Reduced from 50

    print("   ✓ Models initialized successfully")

except Exception as e:
    logger.error(f"✗ Failed to initialize models: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =====================================================================
# 2. Load PDF Documents
# =====================================================================
try:
    print("\n[3/6] Loading Documents...")
    pdf_dir = Path("data")
    
    if not pdf_dir.exists():
        logger.error(f"Data directory not found: {pdf_dir.absolute()}")
        sys.exit(1)

    files = list(pdf_dir.glob("*"))
    pdf_files = [f for f in files if f.suffix.lower() in ['.pdf', '.txt']]
    
    if not pdf_files:
        logger.error("No PDF or text files found in data directory")
        sys.exit(1)

    print(f"   Found {len(pdf_files)} PDF/text file(s)")

    # Load documents with proper chunking
    all_documents = SimpleDirectoryReader(str(pdf_dir), recursive=True).load_data()
    
    if not all_documents:
        logger.warning("No documents loaded from data directory")
        sys.exit(1)

    # FAST MODE: Use 20-30 chunks for quick testing
    PAGE_LIMIT = int(os.getenv("PAGE_LIMIT", 20))  # Default: 20 for fast mode
    documents = all_documents[:PAGE_LIMIT] if PAGE_LIMIT else all_documents
    
    print(f"   ✓ Loaded {len(all_documents)} total chunks")
    print(f"   ✓ Using {len(documents)} chunks (FAST MODE)")
    print(f"   Expected time: 2-10 minutes on CPU\n")

except Exception as e:
    logger.error(f"Failed to load documents: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =====================================================================
# 3. Connect to Neo4j
# =====================================================================
try:
    print("[4/6] Connecting to Neo4j...")

    neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "Disha@2003")
    neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")

    print(f"   Connecting to {neo4j_url}...")

    graph_store = Neo4jPropertyGraphStore(
        username=neo4j_username,
        password=neo4j_password,
        url=neo4j_url,
    )
    print("   ✓ Neo4j graph store initialized")

except Exception as e:
    logger.error(f"✗ Failed to connect to Neo4j: {e}")
    print("   Make sure Neo4j is running: restart_neo4j.bat")
    sys.exit(1)

# =====================================================================
# 4. Build Knowledge Graph - FAST MODE
# =====================================================================
try:
    print("\n[5/6] Building Knowledge Graph (FAST MODE)...")
    
    # AGGRESSIVE OPTIMIZATIONS FOR FAST MODE
    kg_extractor = SimpleLLMPathExtractor(
        llm=llm,
        max_paths_per_chunk=1,  # MINIMUM for fastest speed
        num_workers=1,
    )

    print(f"   Processing {len(documents)} chunks...")
    print("   " + "-" * 60)
    
    start_time = time.time()
    
    index = PropertyGraphIndex.from_documents(
        documents,
        property_graph_store=graph_store,
        kg_extractors=[kg_extractor],
        show_progress=True,
    )

    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print("   " + "-" * 60)
    print(f"   ✓ Knowledge Graph built successfully!")
    print(f"   ✓ Time taken: {minutes}m {seconds}s")

except Exception as e:
    logger.error(f"✗ Failed to build knowledge graph: {e}")
    if "ReadTimeout" in str(e):
        print("\n   TIMEOUT: Try increasing PAGE_LIMIT in .env")
        print("   Or use the standard pipeline: python rag_pipeline.py")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =====================================================================
# 5. Create Query Engine
# =====================================================================
try:
    print("\n[6/6] Creating Query Engine...")
    query_engine = index.as_query_engine(similarity_top_k=5, llm=llm)
    print("   ✓ Query engine created successfully")

except Exception as e:
    logger.error(f"✗ Failed to create query engine: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =====================================================================
# 6. Test Queries
# =====================================================================
def ask_chatbot(question: str):
    """Query the knowledge graph chatbot."""
    try:
        print(f"\n  Q: {question}")
        response = query_engine.query(question)
        print(f"  A: {str(response)[:300]}...")
        return response
    except Exception as e:
        logger.error(f"Error querying chatbot: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  TEST QUERIES - FAST MODE")
    print("=" * 70)

    try:
        print("\n  Starting test queries...\n")
        
        ask_chatbot("What are the main topics in this document?")

        print("\n" + "=" * 70)
        print("  ✓ FAST MODE PIPELINE COMPLETED!")
        print("=" * 70)
        
        print("\n  Next Steps:")
        print("     - Neo4j Browser: http://localhost:7474")
        print("     - For full pipeline: python rag_pipeline.py")
        print()

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
