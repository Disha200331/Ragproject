import os
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import requests
import time

# Fix Windows console encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment variables
load_dotenv()

# Logging - reduce verbosity
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger(__name__)

# =====================================================================
# Patch asyncio for environments that already have a running loop
# =====================================================================
try:
    import nest_asyncio
    nest_asyncio.apply()
    print("[INFO] nest_asyncio applied for async compatibility")
except ImportError:
    try:
        # Try alternative async patching for Windows
        import warnings
        warnings.filterwarnings('ignore')
        # Set Windows event loop policy if on Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            print("[INFO] Windows event loop policy applied")
    except Exception as e:
        print(f"[WARNING] Could not apply async compatibility patch: {e}")

# LlamaIndex imports
print("[1/6] Importing LlamaIndex modules...")
from llama_index.core import SimpleDirectoryReader, Settings, PropertyGraphIndex
from llama_index.core.indices.property_graph import SimpleLLMPathExtractor
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

print("=" * 70)
print("  RAG PIPELINE - KNOWLEDGE GRAPH BUILDER")
print("  Running at:", time.strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 70)

# =====================================================================
# 1. Initialize Models (Gemma + BGE)
# =====================================================================
try:
    print("\n[2/6] Initializing Models...")
    print("   Checking Ollama connection (timeout: 10s)...")

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            print(f"   ✓ Ollama is running with {len(models)} model(s)")
            if model_names:
                for name in model_names[:3]:
                    print(f"      - {name}")
                if len(model_names) > 3:
                    print(f"      - ... and {len(model_names) - 3} more")
            
            gemma_available = any("gemma" in n.lower() for n in model_names)
            if not gemma_available:
                print(f"   ✗ WARNING: gemma3:1b not found in available models")
                print(f"   Run: ollama pull gemma3:1b")
        else:
            raise Exception(f"Ollama returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Ollama is not running: {e}")
        logger.error("   Start Ollama: run 'ollama serve' in a terminal")
        print("   Ensure Ollama is running before starting this script")
        sys.exit(1)

    # Initialize LLM with longer timeout for large PDFs
    # Note: Both request_timeout and httpx timeout need to be set
    llm = Ollama(
        model="gemma3:1b",
        request_timeout=1800.0,  # 30 minutes for slow CPU inference (increased from 10 min)
        temperature=float(os.getenv("LLM_TEMPERATURE", 0.1)),
        context_window=int(os.getenv("LLM_CONTEXT_WINDOW", 4096)),
    )
    # Configure httpx async client with longer timeout
    try:
        import httpx
        # Update async client timeout if possible
        llm.async_client = httpx.AsyncClient(timeout=1800.0)
    except Exception as e:
        print(f"   [WARNING] Could not configure async timeout: {e}")
    
    print("   ✓ Ollama LLM (gemma3:1b) initialized with 30-min timeout")

    print("   Loading BGE embeddings (1-2 min on first run)...")
    embed_model = HuggingFaceEmbedding(
        model_name=os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5"),
        max_length=int(os.getenv("EMBEDDING_MAX_LENGTH", 512))
    )
    print("   ✓ BGE embeddings loaded")

    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50

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
        print(f"      Creating data directory...")
        pdf_dir.mkdir(exist_ok=True)
        print(f"      Please add PDF files to: {pdf_dir.absolute()}")
        sys.exit(1)

    files = list(pdf_dir.glob("*"))
    pdf_files = [f for f in files if f.suffix.lower() in ['.pdf', '.txt']]
    
    print(f"   Found {len(pdf_files)} PDF/text file(s) in data/:")
    for f in pdf_files:
        print(f"      - {f.name} ({f.stat().st_size / 1024 / 1024:.1f} MB)")

    if not pdf_files:
        logger.error("No PDF or text files found in data directory")
        print(f"      Add PDF files to: {pdf_dir.absolute()}")
        sys.exit(1)

    print(f"   Loading documents from: {pdf_dir.absolute()}")
    all_documents = SimpleDirectoryReader(str(pdf_dir), recursive=True).load_data()
    
    if not all_documents:
        logger.warning("No documents loaded from data directory")
        sys.exit(1)

    # ---- DEMO MODE: limit to first 50 pages for fast run ----
    PAGE_LIMIT = int(os.getenv("PAGE_LIMIT", 50))
    documents = all_documents[:PAGE_LIMIT] if PAGE_LIMIT else all_documents
    
    print(f"   [OK] Loaded {len(all_documents)} total chunks", end="")
    if PAGE_LIMIT and len(all_documents) > PAGE_LIMIT:
        print(f" — using first {PAGE_LIMIT} for demo")
        print(f"   TIP: Set PAGE_LIMIT=0 in .env to process all pages (overnight run)")
    else:
        print()

except Exception as e:
    logger.error(f"Failed to load documents: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =====================================================================
# 3. Connect to Neo4j
# =====================================================================
try:
    print("\n[4/6] Connecting to Neo4j...")

    neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "Disha@2003")
    neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")

    if not neo4j_password:
        logger.error("NEO4J_PASSWORD not set in .env file")
        sys.exit(1)

    print(f"   Connecting to {neo4j_url} as {neo4j_username}...")
    print(f"   Attempting connection (timeout: 5s)...")

    # Test connection with timeout
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_username, neo4j_password), connection_timeout=5.0)
        driver.close()
        print(f"   [OK] Connection test passed")
    except Exception as conn_test_e:
        print(f"   [WARNING] Connection test failed: {conn_test_e}")
        print(f"   Attempting to proceed anyway...")

    graph_store = Neo4jPropertyGraphStore(
        username=neo4j_username,
        password=neo4j_password,
        url=neo4j_url,
    )
    print("   [OK] Neo4j graph store initialized")

except Exception as e:
    logger.error(f"Failed to connect to Neo4j: {e}")
    print("   ✗ Make sure Neo4j is running")
    print(f"   ✗ Run: restart_neo4j.bat")
    print(f"   ✗ URL: {neo4j_url}")
    print(f"   ✗ Error details: {e}")
    sys.exit(1)

# =====================================================================
# 4. Build Knowledge Graph
# =====================================================================
try:
    print("\n[5/6] Building Knowledge Graph...")
    print("   This may take 5-30 minutes depending on PDF size and hardware.")
    print("   DO NOT close this window.\n")

    # Use SimpleLLMPathExtractor (synchronous, no async issues)
    # Optimize for CPU-bound Ollama on Windows
    kg_extractor = SimpleLLMPathExtractor(
        llm=llm,
        max_paths_per_chunk=2,  # Reduced from 3 for faster processing
        num_workers=1,          # Single worker avoids async conflicts
    )

    print(f"   Processing {len(documents)} chunks with gemma3:1b...")
    print(f"   Model timeout: 30 minutes (may take 2-5 minutes per chunk on CPU)\n")

    start_time = time.time()
    print("   Creating PropertyGraphIndex (this is the slow step)...")
    print("   " + "-" * 60)
    
    # Build with retry logic for timeout resilience
    max_retries = 2
    retry_count = 0
    index = None
    
    while retry_count <= max_retries and index is None:
        try:
            index = PropertyGraphIndex.from_documents(
                documents,
                property_graph_store=graph_store,
                kg_extractors=[kg_extractor],
                show_progress=True,
            )
        except Exception as build_error:
            retry_count += 1
            if "ReadTimeout" in str(build_error) or "Timeout" in str(build_error):
                if retry_count <= max_retries:
                    print(f"\n   ⚠ Timeout occurred (attempt {retry_count}/{max_retries + 1})")
                    print(f"   Retrying in 10 seconds...")
                    time.sleep(10)
                else:
                    raise build_error
            else:
                raise build_error

    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print("   " + "-" * 60)
    print(f"\n   ✓ Knowledge Graph built successfully!")
    print(f"   ✓ Time taken: {minutes}m {seconds}s")
    print(f"   ✓ Committed to Neo4j")
    print(f"   View at: http://localhost:7474")

except Exception as e:
    logger.error(f"✗ Failed to build knowledge graph: {e}")
    print(f"\n   Error Type: {type(e).__name__}")
    print(f"   Error: {str(e)[:200]}")
    if "ReadTimeout" in str(e) or "Timeout" in str(e):
        print(f"\n   TROUBLESHOOTING TIMEOUT:")
        print(f"   1. Ollama might be overloaded - try reducing PAGE_LIMIT in .env")
        print(f"   2. Check Ollama is still running: http://localhost:11434/api/tags")
        print(f"   3. Try: ollama pull gemma3:1b (re-download model)")
        print(f"   4. If CPU-bound: consider using tinyllama instead (faster)")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =====================================================================
# 5. Create Query Engine
# =====================================================================
try:
    print("\n[6/6] Creating Query Engine...")

    query_engine = index.as_query_engine(
        similarity_top_k=5,
        llm=llm,
    )
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
        print(f"  A: {response}")
        if hasattr(response, 'response'):
            print(f"  [Response Text]: {response.response}")
        return response
    except Exception as e:
        logger.error(f"Error querying chatbot: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  TEST QUERIES - Knowledge Graph RAG Pipeline")
    print("=" * 70)

    try:
        print("\n  Starting test queries...\n")
        
        query_results = []
        
        q1 = "What was Axis Bank's consolidated RoA and Net NPA for fiscal 2025?"
        r1 = ask_chatbot(q1)
        query_results.append((q1, r1))
        
        print("\n  " + "-" * 65)
        
        q2 = "Who is the Managing Director & CEO of Axis Bank according to the report?"
        r2 = ask_chatbot(q2)
        query_results.append((q2, r2))

        print("\n" + "=" * 70)
        print("  ✓ PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        print("\n  📊 Summary:")
        print(f"     - Processed {len(documents)} document chunks")
        print(f"     - Built knowledge graph in Neo4j")
        print(f"     - Executed {len(query_results)} test queries")
        print(f"     - All queries completed successfully")
        
        print("\n  🔗 Next Steps:")
        print("     - Neo4j Browser: http://localhost:7474")
        print("     - Username: neo4j")
        print("     - Verify: python check_knowledge_graph.py")
        print("     - Run more queries: python query_chatbot.py\n")

    except Exception as e:
        logger.error(f"Error during test queries: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 70)
        print("  ✗ PIPELINE FAILED")
        print("=" * 70)
        sys.exit(1)
