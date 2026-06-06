#!/usr/bin/env python3
"""
Interactive RAG chatbot - query your indexed documents.

Loads the persisted vector index (default) or Neo4j graph index.

Usage:
  python query_chatbot.py
  python query_chatbot.py --mode graph
"""

import argparse
import sys

import rag_config as cfg

cfg.fix_windows_encoding()
cfg.apply_async_compat()


def load_vector_engine(llm):
    from llama_index.core import StorageContext, load_index_from_storage

    if not cfg.STORAGE_DIR.exists():
        raise FileNotFoundError(
            "No vector index found. Run first: python rag_pipeline.py"
        )
    storage_context = StorageContext.from_defaults(persist_dir=str(cfg.STORAGE_DIR))
    index = load_index_from_storage(storage_context)
    return cfg.create_query_engine(index, llm)


def load_graph_engine(llm):
    from llama_index.core import PropertyGraphIndex

    cfg.check_neo4j()
    graph_store = cfg.get_neo4j_graph_store()
    index = PropertyGraphIndex.from_existing(
        property_graph_store=graph_store,
        llm=llm,
    )
    return cfg.create_query_engine(index, llm)


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive RAG chatbot")
    parser.add_argument(
        "--mode",
        choices=["vector", "graph"],
        default="vector",
        help="vector = persisted embedding index; graph = Neo4j knowledge graph",
    )
    args = parser.parse_args()

    print("=" * 70)
    print(f"  RAG CHATBOT ({args.mode} mode)")
    print("=" * 70)

    try:
        cfg.check_ollama()
        llm = cfg.init_llm()
        embed_model = cfg.init_embeddings()
        cfg.configure_settings(llm, embed_model)
    except Exception as e:
        print(f"Setup failed: {e}")
        return 1

    try:
        query_engine = (
            load_graph_engine(llm) if args.mode == "graph" else load_vector_engine(llm)
        )
    except Exception as e:
        print(f"Could not load index: {e}")
        if args.mode == "vector":
            print("Run: python rag_pipeline.py")
        else:
            print("Run: python rag_pipeline.py --mode graph")
        return 1

    print("\nReady. Type a question (or 'quit' to exit).\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            print("Goodbye.")
            break

        try:
            response = query_engine.query(question)
            answer = getattr(response, "response", str(response))
            print(f"\nBot: {answer}\n")
        except Exception as e:
            print(f"\nError: {e}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
