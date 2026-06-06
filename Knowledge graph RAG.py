#!/usr/bin/env python3
"""
RAG Pipeline - vector (default) or graph mode.

Vector mode: embed documents, retrieve chunks, generate answers (fast, reliable).
Graph mode: build a Neo4j knowledge graph, then query it (slower, richer).

Usage:
  python rag_pipeline.py                  # vector mode (recommended)
  python rag_pipeline.py --mode graph     # Neo4j knowledge graph
  python rag_pipeline.py --rebuild        # force re-index
"""

import argparse
import logging
import sys
import time

import rag_config as cfg

cfg.fix_windows_encoding()
cfg.apply_async_compat()

logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger(__name__)

TEST_QUERIES = [
    "What was Axis Bank's consolidated RoA and Net NPA for fiscal 2025?",
    "Who is the Managing Director & CEO of Axis Bank according to the report?",
]


def build_vector_index(documents, rebuild: bool):
    """Build or load a persisted vector index."""
    from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage

    if not rebuild and cfg.STORAGE_DIR.exists():
        print("   Loading existing vector index from storage/...")
        storage_context = StorageContext.from_defaults(persist_dir=str(cfg.STORAGE_DIR))
        return load_index_from_storage(storage_context)

    print(f"   Building vector index from {len(documents)} chunks...")
    index = VectorStoreIndex.from_documents(documents, show_progress=True)
    cfg.STORAGE_DIR.mkdir(exist_ok=True)
    index.storage_context.persist(persist_dir=str(cfg.STORAGE_DIR))
    print("   Index saved to storage/")
    return index


def build_graph_index(documents, llm):
    """Build a Neo4j property graph index."""
    from llama_index.core import PropertyGraphIndex
    from llama_index.core.indices.property_graph import SimpleLLMPathExtractor

    graph_store = cfg.get_neo4j_graph_store()
    kg_extractor = SimpleLLMPathExtractor(
        llm=llm,
        max_paths_per_chunk=2,
        num_workers=1,
    )

    print(f"   Building knowledge graph from {len(documents)} chunks...")
    print("   This may take several minutes on CPU. Do not close this window.\n")

    start = time.time()
    index = PropertyGraphIndex.from_documents(
        documents,
        property_graph_store=graph_store,
        kg_extractors=[kg_extractor],
        show_progress=True,
    )
    elapsed = int(time.time() - start)
    print(f"   Graph built in {elapsed // 60}m {elapsed % 60}s")
    print("   View at: http://localhost:7474")
    return index


def load_graph_index(llm):
    """Load an existing graph index from Neo4j."""
    from llama_index.core import PropertyGraphIndex

    graph_store = cfg.get_neo4j_graph_store()
    return PropertyGraphIndex.from_existing(
        property_graph_store=graph_store,
        llm=llm,
    )


def run_queries(query_engine, questions: list[str]) -> None:
    """Run test queries and print answers."""
    for i, question in enumerate(questions, 1):
        print(f"\n  [{i}/{len(questions)}] Q: {question}")
        response = query_engine.query(question)
        answer = getattr(response, "response", str(response))
        print(f"  A: {answer}")


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG pipeline for document Q&A")
    parser.add_argument(
        "--mode",
        choices=["vector", "graph"],
        default="vector",
        help="vector = fast embedding RAG (default); graph = Neo4j knowledge graph",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild index instead of loading existing",
    )
    parser.add_argument(
        "--page-limit",
        type=int,
        default=None,
        help="Max document chunks to process (default: PAGE_LIMIT from .env)",
    )
    parser.add_argument(
        "--query-only",
        action="store_true",
        help="Skip indexing; load existing index and run test queries only",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  RAG PIPELINE")
    print(f"  Mode: {args.mode.upper()}  |  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Check Ollama
    print("\n[1/5] Checking Ollama...")
    try:
        models = cfg.check_ollama()
        print(f"   OK - {len(models)} model(s), using {cfg.OLLAMA_MODEL}")
    except Exception as e:
        print(f"   FAILED: {e}")
        print("   Start Ollama: ollama serve")
        return 1

    # 2. Init models
    print("\n[2/5] Initializing models...")
    try:
        llm = cfg.init_llm()
        embed_model = cfg.init_embeddings()
        cfg.configure_settings(llm, embed_model)
        print("   OK - LLM and embeddings ready")
    except Exception as e:
        print(f"   FAILED: {e}")
        return 1

    # 3. Load documents (skip if query-only in vector mode with existing storage)
    documents = None
    total_chunks = 0
    skip_load = (
        args.query_only
        and args.mode == "vector"
        and cfg.STORAGE_DIR.exists()
        and not args.rebuild
    )

    if skip_load:
        print("\n[3/5] Skipping document load (using persisted index)")
    else:
        print("\n[3/5] Loading documents...")
        try:
            files = cfg.ensure_data_dir()
            for f in files:
                size_mb = f.stat().st_size / 1024 / 1024
                print(f"   - {f.name} ({size_mb:.1f} MB)")

            documents, total_chunks = cfg.load_documents(args.page_limit)
            print(f"   OK - using {len(documents)} of {total_chunks} chunks")
        except Exception as e:
            print(f"   FAILED: {e}")
            return 1

    # 4. Build or load index
    print(f"\n[4/5] {'Loading' if args.query_only else 'Building'} index ({args.mode})...")
    try:
        if args.mode == "graph":
            cfg.check_neo4j()
            print("   OK - Neo4j connected")
            if args.query_only and not args.rebuild:
                index = load_graph_index(llm)
                print("   OK - loaded existing graph from Neo4j")
            else:
                index = build_graph_index(documents, llm)
        else:
            if args.query_only and not args.rebuild:
                index = build_vector_index([], rebuild=False)
                print("   OK - loaded persisted vector index")
            else:
                index = build_vector_index(documents, rebuild=args.rebuild)
                print("   OK - vector index ready")
    except Exception as e:
        print(f"   FAILED: {e}")
        if args.mode == "graph":
            print("   Start Neo4j: restart_neo4j.bat")
        logger.exception("Index step failed")
        return 1

    # 5. Query
    print("\n[5/5] Running test queries...")
    try:
        query_engine = cfg.create_query_engine(index, llm)
        run_queries(query_engine, TEST_QUERIES)
    except Exception as e:
        print(f"   FAILED: {e}")
        logger.exception("Query step failed")
        return 1

    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\n  Next steps:")
    print("    python query_chatbot.py              # ask more questions")
    if args.mode == "graph":
        print("    python check_knowledge_graph.py      # inspect Neo4j graph")
        print("    http://localhost:7474                # Neo4j browser")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
