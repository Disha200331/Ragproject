import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

print("=" * 60)
print("DIAGNOSTIC CHECKS")
print("=" * 60)

# 1. Check data directory
print("\n1. Checking data directory...")
pdf_dir = Path("data")
if pdf_dir.exists():
    files = list(pdf_dir.glob("*"))
    print(f"   ✅ Data directory exists with {len(files)} file(s)")
    if files:
        for f in files:
            print(f"      - {f.name}")
else:
    print(f"   ❌ Data directory NOT found at {pdf_dir.absolute()}")

# 2. Check Neo4j credentials
print("\n2. Checking Neo4j configuration...")
neo4j_username = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")
neo4j_url = os.getenv("NEO4J_URL")

print(f"   Username: {neo4j_username}")
print(f"   Password: {'*' * len(neo4j_password) if neo4j_password else 'NOT SET'}")
print(f"   URL: {neo4j_url}")

if neo4j_password:
    print("   ✅ Neo4j credentials configured")
else:
    print("   ❌ NEO4J_PASSWORD not set")

# 3. Test Neo4j connection
print("\n3. Testing Neo4j connection (timeout: 5s)...")
try:
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        neo4j_url,
        auth=(neo4j_username, neo4j_password),
        connection_acquisition_timeout=5.0
    )
    with driver.session() as session:
        result = session.run("RETURN 1 as test")
        print(f"   ✅ Successfully connected to Neo4j")
        driver.close()
except Exception as e:
    print(f"   ❌ Failed to connect to Neo4j: {str(e)}")
    print(f"      Make sure Neo4j is running at {neo4j_url}")

# 4. Test Ollama connection
print("\n4. Testing Ollama connection (timeout: 5s)...")
try:
    import requests
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        models = response.json().get("models", [])
        print(f"   ✅ Ollama is running with {len(models)} model(s)")
        gemma_available = any("gemma" in m.get("name", "").lower() for m in models)
        if gemma_available:
            print(f"      ✅ Gemma2 model is available")
        else:
            print(f"      ⚠️  Gemma2 model not found. Available models:")
            for m in models:
                print(f"         - {m.get('name')}")
    else:
        print(f"   ❌ Ollama returned status code {response.status_code}")
except Exception as e:
    print(f"   ❌ Failed to connect to Ollama: {str(e)}")
    print(f"      Make sure Ollama is running at http://localhost:11434")

# 5. Test HuggingFace embedding model
print("\n5. Testing HuggingFace embedding model...")
try:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    print("   Loading BAAI/bge-large-en-v1.5 (this may take a moment)...")
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
    print(f"   ✅ Embedding model loaded successfully")
except Exception as e:
    print(f"   ❌ Failed to load embedding model: {str(e)}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
