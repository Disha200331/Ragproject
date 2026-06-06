import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import asyncio

load_dotenv()

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports
from llama_index.core import SimpleDirectoryReader, Settings, PropertyGraphIndex
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

print("=" * 70)
print("RAG PIPELINE - KNOWLEDGE GRAPH BUILDER")
print("=" * 70)

# Initialize Models
try:
    print("\n[1/5] Initializing Models...")
    requests.get("http://localhost:11434/api/tags", timeout=20)
    
    llm = Ollama(model="gemma3:1b", request_timeout=300.0, context_window=4096, temperature=0.1)
    print("   ✅ Ollama LLM initialized")
    
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
    print("   ✅ BGE embeddings loaded")
    
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50
except Exception as e:
    logger.error(f"Failed to initialize models: {e}")
    sys.exit(1)

# Load Documents
try:
    print("\n[2/5] Loading Documents...")
    pdf_dir = Path("data")
    documents = SimpleDirectoryReader(str(pdf_dir)).load_data()
    print(f"   ✅ Loaded {len(documents)} document(s)")
except Exception as e:
    logger.error(f"Failed to load documents: {e}")
    sys.exit(1)

# Connect to Neo4j
try:
    print("\n[3/5] Connecting to Neo4j...")
    neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "Disha@2003")
    neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
    
    graph_store = Neo4jPropertyGraphStore(
        username=neo4j_username,
        password=neo4j_password,
        url=neo4j_url
    )
    print("   ✅ Connected to Neo4j")
except Exception as e:
    logger.error(f"Failed to connect to Neo4j: {e}")
    sys.exit(1)

# Build Knowledge Graph
print("\n[4/5] Building Knowledge Graph...")
print("   (This may take 5-15 minutes - DO NOT close this window)")

try:
    allowed_entities = ["ORGANIZATION", "PERSON", "FINANCIAL_METRIC", "KPI", "STRATEGY", "DATE"]
    allowed_relations = ["REPORTED", "MANAGED_BY", "ACHIEVED", "PARTNERED_WITH", "TARGETED", "ALLOCATED_TO"]
    
    kg_extractor = SchemaLLMPathExtractor(
        llm=llm,
        possible_entities=allowed_entities,
        possible_relations=allowed_relations,
        strict=False
    )
    
    print("   Creating index (may take a few minutes)...")
    index = PropertyGraphIndex.from_documents(
        documents,
        property_graph_store=graph_store,
        kg_extractors=[kg_extractor],
        show_progress=True
    )
    print("   ✅ Knowledge Graph built successfully!")
    
except Exception as e:
    logger.error(f"Failed to build knowledge graph: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Query Engine
try:
    print("\n[5/5] Creating Query Engine...")
    query_engine = index.as_query_engine(
        similarity_top_k=5,
        llm=llm
    )
    print("   ✅ Query engine created")
except Exception as e:
    logger.error(f"Failed to create query engine: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
print("=" * 70)
print("\nYour knowledge graph is ready at:")
print("  - Web UI: http://localhost:7474")
print("  - Username: neo4j")
print("\nRun 'python check_knowledge_graph.py' to verify nodes/relationships")
print("\n")
