"""
Proteus Vector Store Layer
==========================
OracleVS setup, embedding model initialisation, index helpers,
and convenience functions for creating the five semantic memory stores.
"""

import logging
import oracledb
from langchain_oracledb.vectorstores import OracleVS
from langchain_oracledb.vectorstores.oraclevs import create_index
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.utils import DistanceStrategy

from proteus import config

# Suppress verbose langchain_oracledb logging
logging.getLogger("langchain_oracledb").setLevel(logging.CRITICAL)


def get_embedding_model() -> HuggingFaceEmbeddings:
    """Return the configured HuggingFace embedding model."""
    return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)


def safe_create_index(conn: oracledb.Connection, vs: OracleVS, idx_name: str) -> None:
    """Create an HNSW index, skipping if it already exists."""
    try:
        create_index(
            client=conn,
            vector_store=vs,
            params={"idx_name": idx_name, "idx_type": "HNSW"},
        )
        print(f"  ✅ Created index: {idx_name}")
    except Exception as e:
        if "ORA-00955" in str(e):
            print(f"  ⏭️ Index already exists: {idx_name} (skipped)")
        else:
            raise


def create_vector_store(
    conn: oracledb.Connection,
    embedding_model: HuggingFaceEmbeddings,
    table_name: str,
) -> OracleVS:
    """Create a single OracleVS-backed vector store."""
    return OracleVS(
        client=conn,
        embedding_function=embedding_model,
        table_name=table_name,
        distance_strategy=DistanceStrategy.COSINE,
    )


def create_all_vector_stores(
    conn: oracledb.Connection,
    embedding_model: HuggingFaceEmbeddings,
) -> dict:
    """
    Create all five semantic memory vector stores and their HNSW indexes.

    Returns a dict with keys: knowledge_base_vs, workflow_vs, toolbox_vs,
    entity_vs, summary_vs.
    """
    stores = {}
    table_index_pairs = [
        (config.KNOWLEDGE_BASE_TABLE, "knowledge_base_vs_hnsw", "knowledge_base_vs"),
        (config.WORKFLOW_TABLE, "workflow_vs_hnsw", "workflow_vs"),
        (config.TOOLBOX_TABLE, "toolbox_vs_hnsw", "toolbox_vs"),
        (config.ENTITY_TABLE, "entity_vs_hnsw", "entity_vs"),
        (config.SUMMARY_TABLE, "summary_vs_hnsw", "summary_vs"),
    ]

    print("Creating vector stores and indexes...")
    for table, idx_name, key in table_index_pairs:
        vs = create_vector_store(conn, embedding_model, table)
        safe_create_index(conn, vs, idx_name)
        stores[key] = vs

    print("✅ All vector stores and indexes created!")
    return stores


def ingest_arxiv_papers(
    vector_store: OracleVS,
    max_papers: int = 300,
) -> list[dict]:
    """
    Load papers from the nick007x/arxiv-papers HuggingFace dataset
    and ingest them into the given vector store.

    Returns the list of sampled paper dicts for reuse.
    """
    from datasets import load_dataset

    ds_stream = load_dataset("nick007x/arxiv-papers", split="train", streaming=True)

    sampled_papers = []
    texts = []
    metadata_list = []

    for i, item in enumerate(ds_stream):
        if i >= max_papers:
            break

        arxiv_id = item.get("arxiv_id", f"unknown_{i}")
        title = (item.get("title") or "").strip()
        abstract = (item.get("abstract") or "").strip()
        primary_subject = (item.get("primary_subject") or "").strip()
        authors = item.get("authors") or []

        if isinstance(authors, str):
            authors_text = authors
        elif isinstance(authors, list):
            authors_text = ", ".join(str(a).strip() for a in authors if str(a).strip())
        else:
            authors_text = ""

        text = f"Title: {title}\nAbstract: {abstract}"

        sampled_papers.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": abstract,
            "primary_subject": primary_subject,
            "authors": authors_text,
        })
        texts.append(text)
        metadata_list.append({
            "id": arxiv_id,
            "arxiv_id": arxiv_id,
            "title": title,
            "primary_subject": primary_subject,
            "authors": authors_text,
        })

    vector_store.add_texts(texts=texts, metadatas=metadata_list)
    print(f"✅ Ingested {len(texts)} research papers")
    return sampled_papers


def seed_knowledge_base(knowledge_base_vs: OracleVS, sampled_papers: list[dict]) -> None:
    """Seed the knowledge base vector store with previously ingested papers."""
    if not sampled_papers:
        print("⚠️ No papers to seed — run ingest_arxiv_papers first.")
        return

    kb_texts = [
        f"Title: {p['title']}\nAbstract: {p['abstract']}" for p in sampled_papers
    ]
    kb_meta = [
        {
            "id": p["arxiv_id"],
            "arxiv_id": p["arxiv_id"],
            "title": p["title"],
            "primary_subject": p["primary_subject"],
            "authors": p["authors"],
            "source_type": "arxiv_papers",
        }
        for p in sampled_papers
    ]
    knowledge_base_vs.add_texts(kb_texts, kb_meta)
    print(f"✅ Seeded knowledge base with {len(kb_texts)} arXiv papers")
