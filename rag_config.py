"""Shared configuration and helpers for the RAG pipeline."""

import io
import os
import sys
import logging
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
STORAGE_DIR = Path("storage")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Disha@2003")
PAGE_LIMIT = int(os.getenv("PAGE_LIMIT", "20"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
EMBEDDING_MAX_LENGTH = int(os.getenv("EMBEDDING_MAX_LENGTH", "512"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_CONTEXT_WINDOW = int(os.getenv("LLM_CONTEXT_WINDOW", "4096"))
LLM_REQUEST_TIMEOUT = float(os.getenv("LLM_REQUEST_TIMEOUT", "600.0"))


def fix_windows_encoding() -> None:
    """Avoid UnicodeEncodeError on Windows consoles."""
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )


def apply_async_compat() -> None:
    """Patch asyncio for nested event loops on Windows."""
    try:
        import nest_asyncio

        nest_asyncio.apply()
    except ImportError:
        if sys.platform == "win32":
            import asyncio

            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def check_ollama(model_name: str | None = None) -> list[str]:
    """Verify Ollama is running and return available model names."""
    model_name = model_name or OLLAMA_MODEL
    response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
    response.raise_for_status()
    models = [m.get("name", "") for m in response.json().get("models", [])]
    if not any(model_name.split(":")[0] in n for n in models):
        raise RuntimeError(
            f"Model '{model_name}' not found. Run: ollama pull {model_name}"
        )
    return models


def check_neo4j() -> None:
    """Verify Neo4j is reachable."""
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(
        NEO4J_URL,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        connection_timeout=5.0,
    )
    try:
        driver.verify_connectivity()
    finally:
        driver.close()


def init_llm(model_name: str | None = None):
    """Initialize the Ollama LLM."""
    from llama_index.llms.ollama import Ollama

    model_name = model_name or OLLAMA_MODEL
    llm = Ollama(
        model=model_name,
        base_url=OLLAMA_BASE_URL,
        request_timeout=LLM_REQUEST_TIMEOUT,
        temperature=LLM_TEMPERATURE,
        context_window=LLM_CONTEXT_WINDOW,
    )
    try:
        import httpx

        llm.async_client = httpx.AsyncClient(timeout=LLM_REQUEST_TIMEOUT)
    except Exception:
        pass
    return llm


def init_embeddings():
    """Initialize HuggingFace embedding model."""
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    return HuggingFaceEmbedding(
        model_name=EMBEDDING_MODEL,
        max_length=EMBEDDING_MAX_LENGTH,
    )


def configure_settings(llm, embed_model) -> None:
    """Apply global LlamaIndex settings."""
    from llama_index.core import Settings

    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = CHUNK_SIZE
    Settings.chunk_overlap = CHUNK_OVERLAP


def ensure_data_dir() -> list[Path]:
    """Ensure data directory exists and contains supported files."""
    DATA_DIR.mkdir(exist_ok=True)
    files = [
        f
        for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in {".pdf", ".txt"}
    ]
    if not files:
        raise FileNotFoundError(
            f"No PDF or text files in {DATA_DIR.resolve()}. "
            "Add documents to the data/ folder."
        )
    return files


def load_documents(page_limit: int | None = None):
    """Load and optionally limit document chunks."""
    from llama_index.core import SimpleDirectoryReader

    ensure_data_dir()
    all_documents = SimpleDirectoryReader(str(DATA_DIR), recursive=True).load_data()
    if not all_documents:
        raise RuntimeError("Documents found but none could be loaded.")

    limit = PAGE_LIMIT if page_limit is None else page_limit
    if limit and len(all_documents) > limit:
        return all_documents[:limit], len(all_documents)
    return all_documents, len(all_documents)


def get_neo4j_graph_store():
    """Create a Neo4j property graph store."""
    from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

    return Neo4jPropertyGraphStore(
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        url=NEO4J_URL,
    )


def create_query_engine(index, llm):
    """Create a query engine with a prompt tuned for financial Q&A."""
    from llama_index.core import PromptTemplate

    qa_prompt = PromptTemplate(
        "Context information is below.\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Answer the question using only the context above. "
        "Include all relevant numbers, percentages, and names. "
        "If multiple metrics are asked, list each one.\n"
        "Question: {query_str}\n"
        "Answer: "
    )
    return index.as_query_engine(
        similarity_top_k=5,
        llm=llm,
        text_qa_template=qa_prompt,
    )
