#!/usr/bin/env python3
"""
Verify RAG Pipeline Setup - Check all dependencies and services
"""

import sys
import os
from pathlib import Path

print("\n" + "=" * 70)
print("  RAG PIPELINE SETUP VERIFICATION")
print("=" * 70)

# 1. Check Python version
print("\n[1/5] Python Version...")
print(f"   Version: {sys.version}")
if sys.version_info >= (3, 8):
    print("   ✓ Python 3.8+ detected")
else:
    print("   ✗ Python 3.8+ required")
    sys.exit(1)

# 2. Check required packages
print("\n[2/5] Checking Python Packages...")
required_packages = {
    "llama_index": "llama-index",
    "neo4j": "neo4j",
    "dotenv": "python-dotenv",
    "torch": "torch",
    "requests": "requests",
    "pypdf": "pypdf",
}

all_installed = True
for module, package in required_packages.items():
    try:
        __import__(module)
        print(f"   ✓ {package}")
    except ImportError:
        print(f"   ✗ {package} NOT INSTALLED")
        all_installed = False

if not all_installed:
    print("\n   Install missing packages:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# 3. Check data directory
print("\n[3/5] Checking Data Directory...")
data_dir = Path("data")
if data_dir.exists():
    files = list(data_dir.glob("*"))
    pdf_files = [f for f in files if f.suffix.lower() in ['.pdf', '.txt']]
    if pdf_files:
        print(f"   ✓ Data directory found with {len(pdf_files)} PDF/text file(s)")
        for f in pdf_files[:3]:
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"      - {f.name} ({size_mb:.1f} MB)")
    else:
        print(f"   ✗ No PDF files found in data directory")
        print(f"      Add PDFs to: {data_dir.absolute()}")
        sys.exit(1)
else:
    print(f"   ✗ Data directory not found")
    print(f"      Creating: {data_dir.absolute()}")
    data_dir.mkdir()
    sys.exit(1)

# 4. Check .env file
print("\n[4/5] Checking Configuration (.env)...")
env_file = Path(".env")
if env_file.exists():
    print(f"   ✓ .env file found")
    # Load and display config (without passwords)
    from dotenv import load_dotenv
    load_dotenv()
    
    neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    print(f"      - NEO4J_URL: {neo4j_url}")
    print(f"      - NEO4J_USERNAME: {neo4j_user}")
else:
    print(f"   ✗ .env file not found")
    sys.exit(1)

# 5. Check services (optional)
print("\n[5/5] Checking External Services...")

# Check Ollama
try:
    import requests
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        models = response.json().get("models", [])
        print(f"   ✓ Ollama running ({len(models)} model(s))")
    else:
        print(f"   ✗ Ollama not responding properly")
except Exception as e:
    print(f"   ✗ Ollama not running: {e}")
    print(f"      Start: ollama serve")

# Check Neo4j
try:
    from neo4j import GraphDatabase
    neo4j_password = os.getenv("NEO4J_PASSWORD", "")
    if neo4j_password:
        driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password), connection_timeout=3.0)
        driver.close()
        print(f"   ✓ Neo4j running")
    else:
        print(f"   ✗ NEO4J_PASSWORD not set in .env")
except Exception as e:
    print(f"   ✗ Neo4j not running: {e}")
    print(f"      Start: restart_neo4j.bat")

# Summary
print("\n" + "=" * 70)
print("  ✓ SETUP VERIFICATION COMPLETE")
print("=" * 70)
print("\n  Next Steps:")
print("  1. Ensure Ollama is running: ollama serve")
print("  2. Ensure Neo4j is running: restart_neo4j.bat")
print("  3. Run pipeline: python rag_pipeline.py")
print()
