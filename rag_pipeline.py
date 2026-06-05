import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests  # For checking Ollama connectivity

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

# LlamaIndex imports
from llama_index.core import SimpleDirectoryReader, Settings, PropertyGraphIndex
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

# =====================================================================
# 1. Initialize Models (Gemma + BGE)
# =====================================================================
try:
    print("Initializing Gemma LLM and BGE Embeddings...")
    print("   - Checking Ollama connection (timeout: 10s)...")
    
    # Test Ollama connectivity with timeout
    try:
        requests.get("http://localhost:11434/api/tags", timeout=5)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama is not running. Please start Ollama before running this script.")
        logger.error(f"Download from: https://ollama.ai")
        logger.error(f"After installation, run: ollama serve")
        logger.error(f"Then in another terminal: ollama pull gemma2")
        sys.exit(1)
    
    llm = Ollama(model="gemma3:1b", request_timeout=300.0, temperature=0.1)
    print("   ✅ Ollama LLM (Gemma3:1b) initialized")
    
    print("   - Loading BGE embeddings (this may take 1-2 minutes)...")
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
    print("   ✅ BGE embeddings loaded")

    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50
    print("✅ Models initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize models: {e}")
    sys.exit(1)

# =====================================================================
# 2. Load PDF
# =====================================================================
try:
    pdf_dir = Path("data")
    if not pdf_dir.exists():
        logger.error(f"Data directory not found: {pdf_dir}")
        sys.exit(1)

    documents = SimpleDirectoryReader(str(pdf_dir)).load_data()
    if not documents:
        logger.warning("No documents loaded from data directory")
    else:
        print(f"✅ Loaded {len(documents)} document(s)")
except Exception as e:
    logger.error(f"Failed to load documents: {e}")
    sys.exit(1)

# =====================================================================
# 3. Connect to Neo4j
# =====================================================================
try:
    print("Connecting to Neo4j...")

    neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")

    if not neo4j_password:
        logger.error("NEO4J_PASSWORD environment variable not set")
        sys.exit(1)

    graph_store = Neo4jPropertyGraphStore(
        username=neo4j_username,
        password=neo4j_password,
        url=neo4j_url
    )
    print("✅ Connected to Neo4j")
except Exception as e:
    logger.error(f"Failed to connect to Neo4j: {e}")
    sys.exit(1)
# =====================================================================
# 4. Build Knowledge Graph
# =====================================================================
# =====================================================================
# 4. Build Knowledge Graph
# =====================================================================
try:
    print("Building Knowledge Graph...")
    print("   (This may take 5-15 minutes - DO NOT close this window)")

    allowed_entities = ["ORGANIZATION", "PERSON", "FINANCIAL_METRIC", "KPI", "STRATEGY", "DATE"]
    allowed_relations = ["REPORTED", "MANAGED_BY", "ACHIEVED", "PARTNERED_WITH", "TARGETED", "ALLOCATED_TO"]

    kg_extractor = SchemaLLMPathExtractor(
        llm=llm,
        possible_entities=allowed_entities,
        possible_relations=allowed_relations,
        strict=False
    )

    index = PropertyGraphIndex.from_documents(
        documents,
        property_graph_store=graph_store,
        kg_extractors=[kg_extractor],
        show_progress=True
    )
    print("✅ Knowledge Graph committed to Neo4j")
except Exception as e:
    logger.error(f"Failed to build knowledge graph: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =====================================================================
# 5. Query Engine
# =====================================================================
try:
    query_engine = index.as_query_engine(
        sub_retrievers=["vector", "synonym"],
        similarity_top_k=5,
        llm=llm
    )
    print("✅ Query engine created")
except Exception as e:
    logger.error(f"Failed to create query engine: {e}")
    sys.exit(1)

def ask_chatbot(question: str):
    """Query the chatbot with a question"""
    try:
        print(f"\nUser Question: {question}")
        response = query_engine.query(question)
        print(f"Chatbot Response:\n{response}")
        return response
    except Exception as e:
        logger.error(f"Error querying chatbot: {e}")
        return None

# =====================================================================
# 6. Test Queries
# =====================================================================
if __name__ == "__main__":
    try:
        ask_chatbot("What was Axis Bank's consolidated RoA and Net NPA for fiscal 2025?")
        ask_chatbot("Who is the Managing Director & CEO of Axis Bank according to the report?")
        print("\n✅ Pipeline executed successfully")
    except Exception as e:
        logger.error(f"Error during pipeline execution: {e}")
        sys.exit(1)
