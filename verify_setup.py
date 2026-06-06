#!/usr/bin/env python3
"""Verify RAG pipeline setup - dependencies, data, and services."""

import io
import os
import sys
from pathlib import Path

import rag_config as cfg

cfg.fix_windows_encoding()

print("\n" + "=" * 70)
print("  RAG PIPELINE SETUP VERIFICATION")
print("=" * 70)

# 1. Python version
print("\n[1/5] Python Version...")
print(f"   Version: {sys.version}")
if sys.version_info < (3, 8):
    print("   [FAIL] Python 3.8+ required")
    sys.exit(1)
print("   [OK] Python 3.8+ detected")

# 2. Packages
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
        print(f"   [OK] {package}")
    except ImportError:
        print(f"   [FAIL] {package} NOT INSTALLED")
        all_installed = False

if not all_installed:
    print("\n   Install missing packages:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# 3. Data directory
print("\n[3/5] Checking Data Directory...")
try:
    files = cfg.ensure_data_dir()
    print(f"   [OK] Found {len(files)} PDF/text file(s)")
    for f in files[:3]:
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"      - {f.name} ({size_mb:.1f} MB)")
except FileNotFoundError as e:
    print(f"   [FAIL] {e}")
    sys.exit(1)

# 4. .env
print("\n[4/5] Checking Configuration (.env)...")
env_file = Path(".env")
if env_file.exists():
    print("   [OK] .env file found")
    print(f"      - NEO4J_URL: {cfg.NEO4J_URL}")
    print(f"      - OLLAMA_MODEL: {cfg.OLLAMA_MODEL}")
    print(f"      - PAGE_LIMIT: {cfg.PAGE_LIMIT}")
else:
    print("   [WARN] .env not found - using defaults")
    print("   Copy .env.example to .env for custom settings")

# 5. Services
print("\n[5/5] Checking External Services...")

try:
    models = cfg.check_ollama()
    print(f"   [OK] Ollama running ({len(models)} model(s))")
except Exception as e:
    print(f"   [FAIL] Ollama: {e}")
    print("      Start: ollama serve")

try:
    cfg.check_neo4j()
    print("   [OK] Neo4j running")
except Exception as e:
    print(f"   [WARN] Neo4j: {e}")
    print("      Vector mode works without Neo4j.")
    print("      For graph mode, start: restart_neo4j.bat")

print("\n" + "=" * 70)
print("  SETUP VERIFICATION COMPLETE")
print("=" * 70)
print("\n  Run pipeline:")
print("    python rag_pipeline.py              # vector mode (recommended)")
print("    python rag_pipeline.py --mode graph   # Neo4j knowledge graph")
print()
