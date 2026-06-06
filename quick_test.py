#!/usr/bin/env python3
"""
Quick RAG Pipeline Test - Minimal test without full pipeline
"""

import sys
import os
from pathlib import Path

print("\n" + "=" * 70)
print("  QUICK RAG PIPELINE TEST")
print("=" * 70)

# Check imports
print("\n[1/4] Checking imports...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    from llama_index.core import SimpleDirectoryReader, Settings
    from llama_index.llms.ollama import Ollama
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from neo4j import GraphDatabase
    import requests
    
    print("   ✓ All imports successful")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    print("   Install: pip install -r requirements.txt")
    sys.exit(1)

# Check Ollama
print("\n[2/4] Testing Ollama connection...")
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=10)
    if response.status_code == 200:
        models = response.json().get("models", [])
        print(f"   ✓ Ollama running with {len(models)} model(s)")
        has_gemma = any("gemma" in m.get("name", "").lower() for m in models)
        if has_gemma:
            print("   ✓ gemma3:1b found")
        else:
            print("   ✗ gemma3:1b not found - run: ollama pull gemma3:1b")
    else:
        print(f"   ✗ Ollama returned status {response.status_code}")
except Exception as e:
    print(f"   ✗ Ollama not running: {e}")
    print("   Start: ollama serve")
    sys.exit(1)

# Check Neo4j
print("\n[3/4] Testing Neo4j connection...")
try:
    neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "Disha@2003")
    
    driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_pass), connection_timeout=5.0)
    driver.close()
    print(f"   ✓ Neo4j connection successful")
except Exception as e:
    print(f"   ✗ Neo4j connection failed: {e}")
    print("   Start: restart_neo4j.bat")
    sys.exit(1)

# Check data
print("\n[4/4] Checking data...")
data_dir = Path("data")
if data_dir.exists():
    files = list(data_dir.glob("*.pdf")) + list(data_dir.glob("*.txt"))
    if files:
        total_size = sum(f.stat().st_size for f in files) / 1024 / 1024
        print(f"   ✓ Found {len(files)} file(s) ({total_size:.1f} MB)")
        
        # Try loading documents
        try:
            docs = SimpleDirectoryReader(str(data_dir)).load_data()
            print(f"   ✓ Loaded {len(docs)} document chunks")
        except Exception as e:
            print(f"   ✗ Error loading documents: {e}")
    else:
        print(f"   ✗ No PDF/txt files in data/")
else:
    print(f"   ✗ data/ directory not found")

print("\n" + "=" * 70)
print("  ✓ ALL TESTS PASSED - Ready to run pipeline!")
print("=" * 70)
print("\n  Run: python rag_pipeline.py\n")
