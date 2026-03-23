# Lab 2: Build the Memory Engine

## Introduction

In this lab you'll set up the complete memory infrastructure that powers Proteus, SeerGroup's AI research assistant. Starting with a database connection, you'll create vector-enabled tables, ingest research papers from arXiv, build the MemoryManager with seven distinct memory types, and wire up a semantic Toolbox for dynamic tool discovery.

This is the largest lab in the workshop — by the end, you'll have a fully functional memory engine that you can query from Python. Everything you build here is imported from the pre-built `proteus` package, so you'll see the code running and can inspect the source files to understand what's happening under the hood.

**Estimated Time:** 30 minutes

### Objectives

In this lab you will:

1. Connect to Oracle AI Database as the VECTOR user
2. Create a vector-enabled table and ingest 300 arXiv research papers
3. Perform semantic similarity search with natural language queries and metadata filters
4. Create all seven memory tables (conversational, knowledge base, workflow, toolbox, entity, summary, tool log)
5. Initialize the MemoryManager and verify read/write operations
6. Initialize the semantic Toolbox and register a test tool with LLM-augmented discovery

### Prerequisites

This lab assumes you have:

* Completed Lab 1 (database provisioned, VECTOR user created, credentials stored via `%store`)
* Downloaded the `proteus-workshop` package
* Opened `notebooks/lab-2-build-memory-engine.ipynb` in VS Code with the `oracle-agent-env` kernel

### Background

#### Why Memory Engineering Matters

Without memory, a research assistant like Proteus forgets that the user already asked about transformer architectures, can't recall which papers it recommended in the last session, repeats the same search queries it already ran, and loses track of which authors, papers, and research threads have been mentioned.

With proper memory engineering, Proteus can maintain context across long research sessions, reuse proven search-and-analysis patterns from past queries, track entities like paper titles, authors, and research topics across conversations, and compress long conversations while preserving key details.

**Agent Memory** is the exocortex that augments an LLM — capturing, encoding, storing, linking, and retrieving information beyond the model's parametric and contextual limits. It provides the persistence and structure required for long-horizon reasoning and reliable behaviour.

**Memory Engineering** is the scaffolding and control harness that we design to move information optimally and efficiently into, through, and across all components of an AI system (databases, LLMs, applications, etc). It ensures that data is captured, transformed, organized, and retrieved in the right way at the right time — so agents can behave reliably, believably, and capably.

#### The Seven Memory Types

Just like humans have different types of memory (short-term, long-term, procedural), AI agents benefit from specialized memory systems. Here's what we build for Proteus:

| Memory Type | Human Analogy | SeerGroup Use Case | Storage |
|-------------|---------------|-------------------|---------|
| **Conversational** | Short-term memory | "The user asked about transformer architectures for time-series" | SQL Table |
| **Knowledge Base** | Long-term semantic memory | Research papers, web search results, curated references | Vector-Enabled SQL Table |
| **Workflow** | Procedural memory | "Last time someone asked about GANs, we searched arXiv then Tavily" | Vector-Enabled SQL Table |
| **Toolbox** | Skill memory | Available search tools, analysis functions, APIs | Vector-Enabled SQL Table |
| **Entity** | Episodic memory | "Vaswani et al. authored 'Attention Is All You Need' on transformers" | Vector-Enabled SQL Table |
| **Summary** | Compressed memory | "90-minute literature review condensed to 5 bullet points" | Vector-Enabled SQL Table |
| **Tool Log** | Episodic memory | "Full Tavily search output stored in DB, preview in context" | SQL Table |

> **Note on Tool Log:** Tool Log is a form of episodic memory — it records *what happened* during each tool execution. Beyond keeping the context window lean, tool logs can serve as a source from which **procedural memories** (workflow patterns) and **semantic memories** (knowledge base entries) can be distilled over time.

#### Programmatic vs. Agent-Triggered Operations

A key design decision in memory engineering is deciding which operations run **programmatically** (always executed by the harness code) versus **agent-triggered** (the LLM chooses to invoke them during reasoning).

In Proteus's design, the harness is intentionally opinionated: memory loading and persistence are automatic, while external retrieval and context compaction are chosen by the agent.

| Operation | Programmatic | Agent-Triggered | Notes |
|-----------|:------------:|:---------------:|-------|
| `read_conversational_memory()` | ✅ | ❌ | Always loaded at turn start (unsummarized turns only) |
| `read_knowledge_base()` | ✅ | ❌ | Always loaded at turn start |
| `read_workflow()` | ✅ | ❌ | Always loaded at turn start |
| `read_entity()` | ✅ | ❌ | Always loaded at turn start |
| `read_summary_context()` | ✅ | ❌ | Always loaded at turn start (IDs + descriptions) |
| `read_toolbox()` | ✅ | ❌ | Tool schemas retrieved before model reasoning |
| `write_conversational_memory()` | ✅ | ❌ | User message (pre-loop) + assistant answer (post-loop) |
| `write_workflow()` | ✅ | ❌ | Persisted after loop when tool steps exist |
| `write_entity()` | ✅ | ❌ | Best-effort extraction around user/final assistant text |
| `write_tool_log()` | ✅ | ❌ | Full tool output offloaded to DB after every tool execution |
| Tool-call decision (`tool_choice=auto`) | ❌ | ✅ | Model decides whether to call tools |
| `search_tavily()` | ❌ | ✅ | Agent-triggered external retrieval |
| `expand_summary()` | ❌ | ✅ | Agent-triggered just-in-time summary expansion |
| `summarize_and_store()` | ❌ | ✅ | Agent-triggered context compaction primitive |
| `summarize_conversation()` | ❌ | ✅ | Agent-triggered conversation compaction for active thread |

**Why this split works:** (1) Reliability from programmatic memory — critical memory load/save behavior never depends on the model remembering to do it. (2) Adaptivity from agent-triggered tools — the model can selectively fetch, expand, or compact only when needed. (3) Clear control boundaries — the harness owns state integrity; the model owns strategy inside those boundaries.

#### Key Components

- **`OracleVS`**: LangChain abstraction over Oracle vector-enabled SQL tables
- **`HuggingFaceEmbeddings`**: Converts text to 768-dimensional vectors using `sentence-transformers/paraphrase-mpnet-base-v2`
- **`DistanceStrategy.COSINE`**: Measures vector similarity using cosine distance
- **HNSW Index**: Graph-based ANN index for fast and accurate nearest-neighbor retrieval

#### The MemoryManager

The `MemoryManager` class is the central abstraction that unifies all memory operations. Key features include thread-based conversations (messages organized by `thread_id`, one per research session), semantic search across vector stores, metadata filtering (workflows filter by `num_steps > 0`, summaries filter by `id`), LLM-powered entity extraction (automatically extracts paper titles, authors, and research topics from text), and formatted context output (each read method returns text ready for the LLM context window with purpose headers).

There are existing frameworks that abstract memory management: LangChain Memory, Mem0, LlamaIndex, and Zep. Building your own (as we do here) gives you a deep understanding of how memory engineering works. For production, you might consider using or extending an existing framework.

#### The Semantic Toolbox

As your AI system grows, you might have hundreds of tools available. Passing all tools to the LLM at inference time creates context bloat, tool selection failure, increased latency, and higher costs. Model providers typically recommend limiting tools to 10-20 max for reliable selection.

The `Toolbox` class solves this by treating tools as a searchable memory: register hundreds of tools with their descriptions, then at inference time use vector search to find tools semantically relevant to the current query. Only the top 3-5 retrieved tools are passed to the LLM.

The `augment=True` flag triggers LLM-powered enhancement: docstring augmentation (LLM rewrites the docstring to be clearer), synthetic query generation (LLM generates example queries that would need this tool), and rich embedding (combines name + augmented docstring + signature + queries for better retrieval).

This sits at the intersection of three disciplines: *memory engineering* (tools as procedural memory), *context engineering* (only relevant tools in context), and *prompt engineering* (role-setting for better docstring augmentation).

## Task 1: Restore Credentials and Connect

<details><summary>🔍 View source: <code>proteus/db.py</code> — Connection helper with retry logic</summary>

```python
"""
Proteus Database Layer
======================
Connection helpers and DDL for memory tables.
"""

import time
import oracledb
from proteus import config


def connect_to_oracle(
    max_retries: int = 3,
    retry_delay: int = 5,
    user: str = None,
    password: str = None,
    dsn: str = None,
    program: str = "seergroup.proteus.workshop",
) -> oracledb.Connection:
    """Connect to Oracle database with retry logic and helpful error messages."""
    user = user or config.DB_USER
    password = password or config.DB_PASSWORD
    dsn = dsn or config.DB_DSN

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Connection attempt {attempt}/{max_retries}...")
            conn = oracledb.connect(user=user, password=password, dsn=dsn, program=program)
            print("✓ Connected successfully!")

            with conn.cursor() as cur:
                cur.execute("SELECT banner FROM v$version WHERE banner LIKE 'Oracle%'")
                banner = cur.fetchone()[0]
                print(f"\n{banner}")

            return conn

        except oracledb.OperationalError as e:
            error_msg = str(e)
            print(f"✗ Connection failed (attempt {attempt}/{max_retries})")

            if "DPY-4011" in error_msg or "Connection reset by peer" in error_msg:
                print("  → Database may still be starting. Retrying...")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise
            else:
                raise

    raise ConnectionError("Failed to connect after all retries")


# ── DDL helpers ───────────────────────────────────────────

def drop_all_tables(conn: oracledb.Connection) -> None:
    """Drop all memory tables (idempotent)."""
    for table in config.ALL_TABLES:
        try:
            with conn.cursor() as cur:
                cur.execute(f"DROP TABLE {table} PURGE")
            print(f"  ✓ Dropped {table}")
        except Exception as e:
            if "ORA-00942" in str(e):
                print(f"  - {table} (not exists)")
            else:
                print(f"  ✗ {table}: {e}")
    conn.commit()


def create_conversational_history_table(
    conn: oracledb.Connection,
    table_name: str = None,
) -> str:
    """Create the conversational memory SQL table with indexes."""
    table_name = table_name or config.CONVERSATIONAL_TABLE
    with conn.cursor() as cur:
        try:
            cur.execute(f"DROP TABLE {table_name}")
        except Exception:
            pass

        cur.execute(f"""
            CREATE TABLE {table_name} (
                id VARCHAR2(100) DEFAULT SYS_GUID() PRIMARY KEY,
                thread_id VARCHAR2(100) NOT NULL,
                role VARCHAR2(50) NOT NULL,
                content CLOB NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata CLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                summary_id VARCHAR2(100) DEFAULT NULL
            )
        """)
        cur.execute(f"CREATE INDEX idx_{table_name.lower()}_thread_id ON {table_name}(thread_id)")
        cur.execute(f"CREATE INDEX idx_{table_name.lower()}_timestamp ON {table_name}(timestamp)")

    conn.commit()
    print(f"✅ Table {table_name} created with indexes (thread_id, timestamp)")
    return table_name


def create_tool_log_table(
    conn: oracledb.Connection,
    table_name: str = None,
) -> str:
    """Create the tool log SQL table (experimental / episodic memory)."""
    table_name = table_name or config.TOOL_LOG_TABLE
    with conn.cursor() as cur:
        try:
            cur.execute(f"DROP TABLE {table_name}")
        except Exception:
            pass

        cur.execute(f"""
            CREATE TABLE {table_name} (
                id VARCHAR2(100) DEFAULT SYS_GUID() PRIMARY KEY,
                thread_id VARCHAR2(100) NOT NULL,
                tool_call_id VARCHAR2(200) NOT NULL,
                tool_name VARCHAR2(200) NOT NULL,
                tool_args CLOB,
                tool_output CLOB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute(f"CREATE INDEX idx_{table_name.lower()}_thread ON {table_name}(thread_id)")

    conn.commit()
    print(f"✅ Table {table_name} created")
    return table_name

```

**What this code does:** `connect_to_oracle()` establishes a connection to Oracle AI Database using the `oracledb` thin driver. It retries up to 3 times with a configurable delay, which is useful when the database is still starting. On success, it prints the Oracle version banner. The module also contains `drop_all_tables()`, `create_conversational_history_table()`, and `create_tool_log_table()` — DDL helpers used later in Task 6.

</details>


The first cell restores the credentials you saved in Lab 1 using `%store -r` and sets them as environment variables so the `proteus` modules can access them.

1. Run the first two code cells to restore credentials and establish the database connection.

2. You should see a successful connection message with the Oracle version banner.

    > **What's happening:** The `proteus.db.connect_to_oracle()` function uses the `oracledb` thin driver with retry logic. It reads credentials from `os.environ`, which we just populated from the `%store` values.

## Task 2: Initialize Embeddings and Create a Vector Search Demo Table

<details><summary>🔍 View source: <code>proteus/vector_store.py</code> — OracleVS setup, embedding model, and index helpers</summary>

```python
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

```

**What this code does:** `get_embedding_model()` returns a HuggingFace `sentence-transformers/paraphrase-mpnet-base-v2` model that converts text into 768-dimensional vectors. `create_vector_store()` wraps `OracleVS` with cosine distance. `safe_create_index()` creates an HNSW index, skipping gracefully if it already exists. The module also includes `ingest_arxiv_papers()` and `seed_knowledge_base()` used in Tasks 3 and 7.

</details>


1. Run the code cell that imports `get_embedding_model` and creates an `OracleVS` vector store backed by a `VECTOR_SEARCH_DEMO` table.

2. Run the next cell to create an HNSW index on the table.

    > **Key concept:** HNSW (Hierarchical Navigable Small World) is a graph-based approximate nearest-neighbor index. It provides fast, accurate similarity search at scale — essential when your knowledge base grows to thousands of documents.

## Task 3: Ingest Research Papers from arXiv

1. Run the ingestion cell. This loads 300 papers from the `nick007x/arxiv-papers` HuggingFace dataset and stores them with embeddings in the vector table.

    > **🔍 Notice:** This process may take 3-5 minutes as each paper's title and abstract are embedded into 768-dimensional vectors.

2. Run the sample inspection cell to see the metadata fields available for filtering: `primary_subject`, `arxiv_id`, `title`, and `authors`.

## Task 4: Query with Natural Language

1. Run the **basic similarity search** cell. Notice how a query about "planetary exploration mission planning" finds relevant papers even when the exact words don't appear in the titles.

    > **Key concept:** Semantic search finds documents based on *meaning*, not keyword matching. The embedding model converts both the query and the documents into vectors, then measures cosine distance between them.

2. Run the **search with relevance scores** cell. Scores close to 0 indicate high similarity (cosine distance); scores near 1 indicate low relevance.

## Task 5: Filtered Search with Metadata

1. Run the **filter by subject area** cell to see how metadata filters combine with vector similarity.

2. Run the **filter by paper ID** cell to retrieve a specific paper by its arXiv ID.

    > **Key concept:** OracleVS supports metadata filters (`$eq`, `$in`, `$gt`, etc.) that are applied *before* the vector similarity ranking. This is how Proteus narrows results by subject area, author, or date.

## Task 6: Create All Memory Tables and Vector Stores

Now we move from the demo table to the full memory architecture. This creates the seven tables that power Proteus's memory system.

1. Run the cell that calls `drop_all_tables()`, `create_conversational_history_table()`, `create_tool_log_table()`, and `create_all_vector_stores()`.

    > **Architecture note:** Two tables are plain SQL (conversational memory, tool log) because they need exact-match retrieval by thread ID. The other five are vector-enabled for semantic search.

## Task 7: Seed the Knowledge Base

1. Run the cell that calls `seed_knowledge_base()`. This populates the knowledge base vector store with the same arXiv papers — giving Proteus a body of literature to draw from.

    > **🔍 Notice:** This may take 3-5 minutes.

## Task 8: Initialize the MemoryManager

<details><summary>🔍 View source: <code>proteus/memory_manager.py</code> — The complete MemoryManager class — 7 memory types</summary>

```python
"""
Proteus Memory Manager
======================
Unified read/write interface for all seven memory types.
"""

import json as json_lib
from datetime import datetime

from proteus import config


class MemoryManager:
    """
    Memory manager for AI agents using Oracle AI Database.

    Manages 7 types of memory:
    - Conversational: Chat history per research session (SQL table)
    - Knowledge Base: Searchable documents and research papers (vector-enabled SQL table)
    - Workflow: Learned search-and-analysis patterns (vector-enabled SQL table)
    - Toolbox: Available research tools (vector-enabled SQL table)
    - Entity: Paper titles, authors, research topics (vector-enabled SQL table)
    - Summary: Compressed context from long sessions (vector-enabled SQL table)
    - Tool Log: Offloaded tool outputs for lean context (SQL table)
    """

    def __init__(
        self,
        conn,
        conversation_table: str,
        knowledge_base_vs,
        workflow_vs,
        toolbox_vs,
        entity_vs,
        summary_vs,
        tool_log_table: str = None,
    ):
        self.conn = conn
        self.conversation_table = conversation_table
        self.knowledge_base_vs = knowledge_base_vs
        self.workflow_vs = workflow_vs
        self.toolbox_vs = toolbox_vs
        self.entity_vs = entity_vs
        self.summary_vs = summary_vs
        self.tool_log_table = tool_log_table

    # ==================== CONVERSATIONAL MEMORY (SQL) ====================

    def write_conversational_memory(self, content: str, role: str, thread_id: str) -> str:
        """Store a message in conversation history."""
        thread_id = str(thread_id)
        with self.conn.cursor() as cur:
            id_var = cur.var(str)
            cur.execute(
                f"""
                INSERT INTO {self.conversation_table}
                    (thread_id, role, content, metadata, timestamp)
                VALUES (:thread_id, :role, :content, :metadata, CURRENT_TIMESTAMP)
                RETURNING id INTO :id
            """,
                {
                    "thread_id": thread_id,
                    "role": role,
                    "content": content,
                    "metadata": "{}",
                    "id": id_var,
                },
            )
            record_id = id_var.getvalue()[0] if id_var.getvalue() else None
        self.conn.commit()
        return record_id

    def get_unsummarized_messages(self, thread_id: str, limit: int = 100) -> list[dict]:
        """Return unsummarized conversation turns for a thread."""
        thread_id = str(thread_id)
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, role, content, timestamp
                FROM {self.conversation_table}
                WHERE thread_id = :thread_id AND summary_id IS NULL
                ORDER BY timestamp ASC
                FETCH FIRST :limit ROWS ONLY
            """,
                {"thread_id": thread_id, "limit": limit},
            )
            rows = cur.fetchall()

        return [
            {"id": rid, "role": role, "content": content, "timestamp": ts}
            for rid, role, content, ts in rows
        ]

    def read_conversational_memory(self, thread_id: str, limit: int = 10) -> str:
        """Read unsummarized conversation history for a thread.

        NOTE: Only returns messages where summary_id IS NULL. Once messages
        are summarized via summarize_conversation(), they are excluded here
        and replaced by a compact summary reference in Summary Memory.
        """
        messages = self.get_unsummarized_messages(thread_id, limit=limit)
        lines = [
            f"[{m['timestamp'].strftime('%H:%M:%S')}] [{m['role']}] {m['content']}"
            for m in messages
        ]
        messages_formatted = "\n".join(lines)
        return f"""## Conversation Memory (Session: {thread_id})
### Purpose: Recent dialogue turns that have NOT yet been summarized.
### When to use: Refer to this for the user's latest questions, your prior answers,
### and any commitments or follow-ups from the current research session.
### If context grows too long, call summarize_conversation(thread_id) to compact.

{messages_formatted}"""

    def mark_as_summarized(
        self, thread_id: str, summary_id: str, message_ids: list[str] | None = None
    ):
        """Mark conversation turns as summarized."""
        thread_id = str(thread_id)
        with self.conn.cursor() as cur:
            if message_ids:
                cur.executemany(
                    f"""
                    UPDATE {self.conversation_table}
                    SET summary_id = :summary_id
                    WHERE thread_id = :thread_id AND id = :id AND summary_id IS NULL
                    """,
                    [
                        {"summary_id": summary_id, "thread_id": thread_id, "id": mid}
                        for mid in message_ids
                    ],
                )
                count = len(message_ids)
            else:
                cur.execute(
                    f"""
                    UPDATE {self.conversation_table}
                    SET summary_id = :summary_id
                    WHERE thread_id = :thread_id AND summary_id IS NULL
                """,
                    {"summary_id": summary_id, "thread_id": thread_id},
                )
                count = cur.rowcount
        self.conn.commit()
        print(f"  📦 Marked {count} messages as summarized (summary_id: {summary_id})")

    # ==================== KNOWLEDGE BASE (Vector-Enabled SQL Table) ====================

    def write_knowledge_base(self, text: str, metadata: dict):
        """Store text in knowledge base with metadata."""
        self.knowledge_base_vs.add_texts([text], [metadata])

    def read_knowledge_base(self, query: str, k: int = 3) -> str:
        """Search knowledge base for relevant content."""
        results = self.knowledge_base_vs.similarity_search(query, k=k)
        content = "\n".join([doc.page_content for doc in results])
        return f"""## Knowledge Base Memory
### Purpose: Research papers, web search results, and curated references stored for long-term reference.
### When to use: Cite specific facts, findings, or paper details from here before
### resorting to external search. If the KB lacks what you need, use search_tavily() to fetch
### new information (which will be stored here automatically).

{content}"""

    # ==================== WORKFLOW (Vector-Enabled SQL Table) ====================

    def write_workflow(self, query: str, steps: list, final_answer: str, success: bool = True):
        """Store a completed workflow pattern for future reference."""
        steps_text = "\n".join([f"Step {i+1}: {s}" for i, s in enumerate(steps)])
        text = f"Query: {query}\nSteps:\n{steps_text}\nAnswer: {final_answer[:200]}"

        metadata = {
            "query": query,
            "success": success,
            "num_steps": len(steps),
            "timestamp": datetime.now().isoformat(),
        }
        self.workflow_vs.add_texts([text], [metadata])

    def read_workflow(self, query: str, k: int = 3) -> str:
        """Search for similar past workflows with at least 1 step."""
        results = self.workflow_vs.similarity_search(
            query, k=k, filter={"num_steps": {"$gt": 0}}
        )
        if not results:
            return "## Workflow Memory\nNo relevant workflows found."
        content = "\n---\n".join([doc.page_content for doc in results])
        return f"""## Workflow Memory
### Purpose: Step-by-step records of how similar past research queries were resolved.
### When to use: Before planning a multi-step action, check if a similar workflow
### already succeeded. Reuse proven tool sequences instead of re-discovering them.

{content}"""

    # ==================== TOOLBOX (Vector-Enabled SQL Table) ====================

    def write_toolbox(self, text: str, metadata: dict):
        """Store a tool definition in the toolbox."""
        self.toolbox_vs.add_texts([text], [metadata])

    def read_toolbox(self, query: str, k: int = 3) -> list[dict]:
        """Find relevant tools and return OpenAI-compatible schemas."""
        results = self.toolbox_vs.similarity_search(query, k=k)
        tools = []
        for doc in results:
            meta = doc.metadata
            stored_params = meta.get("parameters", {})
            properties = {}
            required = []

            for param_name, param_info in stored_params.items():
                param_type = param_info.get("type", "string")
                type_mapping = {
                    "<class 'str'>": "string",
                    "<class 'int'>": "integer",
                    "<class 'float'>": "number",
                    "<class 'bool'>": "boolean",
                    "str": "string",
                    "int": "integer",
                    "float": "number",
                    "bool": "boolean",
                }
                json_type = type_mapping.get(param_type, "string")
                properties[param_name] = {"type": json_type}

                if "default" not in param_info:
                    required.append(param_name)

            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": meta.get("name", "tool"),
                        "description": meta.get("description", ""),
                        "parameters": {
                            "type": "object",
                            "properties": properties,
                            "required": required,
                        },
                    },
                }
            )
        return tools

    # ==================== ENTITY (Vector-Enabled SQL Table) ====================

    def extract_entities(self, text: str, llm_client) -> list[dict]:
        """Use LLM to extract entities (paper titles, authors, research topics) from text."""
        if not text or len(text.strip()) < 5:
            return []

        prompt = f'''Extract entities from: "{text[:500]}"
Return JSON: [{{"name": "X", "type": "PAPER|AUTHOR|TOPIC|INSTITUTION|METHOD", "description": "brief"}}]
If none: []'''

        try:
            response = llm_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=300,
            )
            result = response.choices[0].message.content.strip()

            start, end = result.find("["), result.rfind("]")
            if start == -1 or end == -1:
                return []

            parsed = json_lib.loads(result[start : end + 1])
            return [
                {
                    "name": e["name"],
                    "type": e.get("type", "UNKNOWN"),
                    "description": e.get("description", ""),
                }
                for e in parsed
                if isinstance(e, dict) and e.get("name")
            ]
        except Exception:
            return []

    def write_entity(
        self, name: str, entity_type: str, description: str, llm_client=None, text: str = None
    ):
        """Store an entity OR extract and store entities from text."""
        if text and llm_client:
            entities = self.extract_entities(text, llm_client)
            for e in entities:
                self.entity_vs.add_texts(
                    [f"{e['name']} ({e['type']}): {e['description']}"],
                    [{"name": e["name"], "type": e["type"], "description": e["description"]}],
                )
            return entities
        else:
            self.entity_vs.add_texts(
                [f"{name} ({entity_type}): {description}"],
                [{"name": name, "type": entity_type, "description": description}],
            )

    def read_entity(self, query: str, k: int = 5) -> str:
        """Search for relevant entities."""
        results = self.entity_vs.similarity_search(query, k=k)
        if not results:
            return "## Entity Memory\nNo entities found."

        entities = [
            f"• {doc.metadata.get('name', '?')}: {doc.metadata.get('description', '')}"
            for doc in results
            if hasattr(doc, "metadata")
        ]
        entities_formatted = "\n".join(entities)
        return f"""## Entity Memory
### Purpose: Named entities (paper titles, authors, research topics, methods) extracted from conversations.
### When to use: Resolve references like "that paper" or "the author we discussed".
### Entity memory provides continuity — ground your answers in known entities
### rather than guessing or re-asking for names already mentioned.

{entities_formatted}"""

    # ==================== SUMMARY (Vector-Enabled SQL Table) ====================

    def write_summary(self, summary_id: str, full_content: str, summary: str, description: str):
        """Store a summary with its original content."""
        self.summary_vs.add_texts(
            [f"{summary_id}: {description}"],
            [
                {
                    "id": summary_id,
                    "full_content": full_content,
                    "summary": summary,
                    "description": description,
                }
            ],
        )
        return summary_id

    def read_summary_memory(self, summary_id: str) -> str:
        """Retrieve a specific summary by ID (just-in-time retrieval)."""
        results = self.summary_vs.similarity_search(
            summary_id, k=5, filter={"id": summary_id}
        )
        if not results:
            return f"Summary {summary_id} not found."
        doc = results[0]
        return doc.metadata.get("summary", "No summary content.")

    def read_summary_context(self, query: str = "", k: int = 10) -> str:
        """Get available summaries for context window (IDs + descriptions only)."""
        results = self.summary_vs.similarity_search(query or "summary", k=k)
        if not results:
            return "## Summary Memory\nNo summaries available."

        lines = [
            "## Summary Memory",
            "### Purpose: Compressed snapshots of older research sessions.",
            "### When to use: These are lightweight pointers. If a summary looks relevant,",
            "### call expand_summary(summary_id) to retrieve the full content just-in-time.",
            "### Do NOT expand all summaries — only expand when you need specific details.",
            "",
        ]
        for doc in results:
            sid = doc.metadata.get("id", "?")
            desc = doc.metadata.get("description", "No description")
            lines.append(f"  • [ID: {sid}] {desc}")
        return "\n".join(lines)

    # ==================== TOOL LOG (SQL - Experimental Memory) ====================

    def write_tool_log(
        self, thread_id: str, tool_call_id: str, tool_name: str, tool_args: str, tool_output: str
    ) -> str:
        """Log a tool call output to the database and return a compact reference."""
        if not self.tool_log_table:
            return tool_output

        with self.conn.cursor() as cur:
            id_var = cur.var(str)
            cur.execute(
                f"""
                INSERT INTO {self.tool_log_table}
                    (thread_id, tool_call_id, tool_name, tool_args, tool_output)
                VALUES (:thread_id, :tool_call_id, :tool_name, :tool_args, :tool_output)
                RETURNING id INTO :id
            """,
                {
                    "thread_id": str(thread_id),
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "tool_output": tool_output,
                    "id": id_var,
                },
            )
            log_id = id_var.getvalue()[0] if id_var.getvalue() else None
        self.conn.commit()

        preview = tool_output[:150].replace("\n", " ")
        return f"[Tool Log {log_id}] {tool_name} executed. Preview: {preview}..."

    def read_tool_log(self, thread_id: str, limit: int = 20) -> list[dict]:
        """Read tool call logs for a thread."""
        if not self.tool_log_table:
            return []
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, tool_call_id, tool_name, tool_args, tool_output, timestamp
                FROM {self.tool_log_table}
                WHERE thread_id = :thread_id
                ORDER BY timestamp DESC
                FETCH FIRST :limit ROWS ONLY
            """,
                {"thread_id": str(thread_id), "limit": limit},
            )
            rows = cur.fetchall()
        return [
            {
                "id": r[0], "tool_call_id": r[1], "tool_name": r[2],
                "tool_args": r[3], "tool_output": r[4], "timestamp": r[5],
            }
            for r in rows
        ]

    # ==================== SUMMARY EXPANSION HELPERS ====================

    def get_messages_by_summary_id(self, summary_id: str) -> list[dict]:
        """Retrieve original messages that were compacted into a given summary."""
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, role, content, timestamp
                FROM {self.conversation_table}
                WHERE summary_id = :summary_id
                ORDER BY timestamp ASC
            """,
                {"summary_id": summary_id},
            )
            rows = cur.fetchall()
        return [
            {"id": rid, "role": role, "content": content, "timestamp": ts}
            for rid, role, content, ts in rows
        ]

```

**What this code does:** The `MemoryManager` class provides a unified read/write interface across all seven memory types. For conversational memory, it uses SQL INSERT/SELECT/UPDATE via `oracledb` cursors. For knowledge base, workflow, toolbox, entity, and summary memory, it delegates to `OracleVS` vector stores for similarity search. Key methods include `write_conversational_memory()` / `read_conversational_memory()` for thread-based chat history, `mark_as_summarized()` for log compaction, `extract_entities()` for LLM-powered entity extraction, `write_tool_log()` for context offloading, and `read_toolbox()` which returns OpenAI-compatible tool schemas from semantic search results.

</details>


1. Run the cell that creates the `MemoryManager` instance, passing it the database connection, conversation table name, and all five vector stores.

2. Run the **smoke test** cells to verify:
    - Writing and reading conversational memory (thread-based chat history)
    - Searching the knowledge base with a natural language query

    > **Key concept:** The MemoryManager provides a unified read/write interface across all seven memory types. Each `read_*` method returns formatted text ready for the LLM context window, with purpose headers that guide the agent's behavior.

## Task 9: Initialize the Toolbox and Register a Test Tool

<details><summary>🔍 View source: <code>proteus/toolbox.py</code> — Semantic tool registry with LLM-augmented registration</summary>

```python
"""
Proteus Toolbox
===============
Semantic tool registry — tools are discovered by meaning, not by name.
Supports LLM-powered docstring augmentation and synthetic query generation
for improved retrieval.
"""

import inspect
import uuid
import json
from typing import Callable, Optional, Union

from pydantic import BaseModel

from proteus import config


def get_embedding(text: str, embedding_model) -> list[float]:
    """Get the embedding for a text using the given embedding model."""
    return embedding_model.embed_query(text)


class ToolMetadata(BaseModel):
    """Metadata for a registered tool."""
    name: str
    description: str
    signature: str
    parameters: dict
    return_type: str


class Toolbox:
    """
    Toolbox for registering, storing, and retrieving tools with LLM-powered augmentation.

    Tools are stored with embeddings for semantic retrieval, allowing Proteus to
    find relevant research tools based on natural language queries.
    """

    def __init__(self, memory_manager, llm_client, embedding_model, model: str = None):
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.embedding_model = embedding_model
        self.model = model or config.OPENAI_MODEL
        self._tools: dict[str, Callable] = {}
        self._tools_by_name: dict[str, Callable] = {}

    def _augment_docstring(self, docstring: str) -> str:
        """Use LLM to improve and expand a tool's docstring for better retrieval."""
        if not docstring.strip():
            return "No description provided."

        prompt = f"""You are a technical writer. Improve the following function docstring to be more clear,
            comprehensive, and useful. Include:
            1. A clear concise summary
            2. Detailed description of what the function does
            3. When to use this function
            4. Any important notes or caveats

            Original docstring:
            {docstring}

            Return ONLY the improved docstring, no other text.
        """

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=500,
        )
        return response.choices[0].message.content.strip()

    def _generate_queries(self, docstring: str, num_queries: int = 5) -> list[str]:
        """Generate synthetic example queries that would lead to using this tool."""
        prompt = f"""Based on the following tool description, generate {num_queries} diverse example queries
            that a user might ask when they need this tool. Make them natural and varied.

            Tool description:
            {docstring}

            Return ONLY a JSON array of strings, like: ["query1", "query2", ...]
        """

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=300,
        )

        try:
            queries = json.loads(response.choices[0].message.content.strip())
            return queries if isinstance(queries, list) else []
        except json.JSONDecodeError:
            return [response.choices[0].message.content.strip()]

    def _get_tool_metadata(self, func: Callable) -> ToolMetadata:
        """Extract metadata from a function for storage and retrieval."""
        sig = inspect.signature(func)

        parameters = {}
        for name, param in sig.parameters.items():
            param_info = {"name": name}
            if param.annotation != inspect.Parameter.empty:
                param_info["type"] = str(param.annotation)
            if param.default != inspect.Parameter.empty:
                param_info["default"] = str(param.default)
            parameters[name] = param_info

        return_type = "Any"
        if sig.return_annotation != inspect.Signature.empty:
            return_type = str(sig.return_annotation)

        return ToolMetadata(
            name=func.__name__,
            description=func.__doc__ or "No description",
            signature=str(sig),
            parameters=parameters,
            return_type=return_type,
        )

    def register_tool(
        self, func: Optional[Callable] = None, augment: bool = False
    ) -> Union[str, Callable]:
        """
        Register a function as a tool in the toolbox.

        Can be used as a decorator or called directly:

            @toolbox.register_tool
            def my_tool(): ...

            @toolbox.register_tool(augment=True)
            def my_enhanced_tool(): ...
        """

        def decorator(f: Callable) -> str:
            docstring = f.__doc__ or ""
            signature = str(inspect.signature(f))
            object_id = uuid.uuid4()
            object_id_str = str(object_id)

            if augment:
                augmented_docstring = self._augment_docstring(docstring)
                queries = self._generate_queries(augmented_docstring)

                embedding_text = (
                    f"{f.__name__} {augmented_docstring} {signature} {' '.join(queries)}"
                )
                embedding = get_embedding(embedding_text, self.embedding_model)

                tool_data = self._get_tool_metadata(f)
                tool_data.description = augmented_docstring

                tool_dict = {
                    "_id": object_id_str,
                    "embedding": embedding,
                    "queries": queries,
                    "augmented": True,
                    **tool_data.model_dump(),
                }
            else:
                embedding = get_embedding(
                    f"{f.__name__} {docstring} {signature}", self.embedding_model
                )
                tool_data = self._get_tool_metadata(f)

                tool_dict = {
                    "_id": object_id_str,
                    "embedding": embedding,
                    "augmented": False,
                    **tool_data.model_dump(),
                }

            self.memory_manager.write_toolbox(
                f"{f.__name__} {docstring} {signature}", tool_dict
            )

            self._tools[object_id_str] = f
            self._tools_by_name[f.__name__] = f
            return object_id_str

        if func is None:
            return decorator
        return decorator(func)

```

**What this code does:** The `Toolbox` class stores tool definitions with embeddings for semantic retrieval. When `augment=True`, `_augment_docstring()` uses the LLM to rewrite the tool's docstring for clarity, and `_generate_queries()` creates synthetic example queries for better discoverability. `_get_tool_metadata()` extracts function signature, parameters, and return type into a `ToolMetadata` Pydantic model. The `register_tool()` method can be used as a decorator (`@toolbox.register_tool(augment=True)`) or called directly. Tools are stored in the toolbox vector store and also kept in `_tools_by_name` for direct execution.

</details>


1. Run the cell that prompts for your **OpenAI API key** (entered securely via `getpass`).

2. Run the cell that creates the `Toolbox` instance and the OpenAI client.

3. Run the cell that registers `lookup_paper_details` with `augment=True`. Watch the output — the LLM rewrites the docstring and generates synthetic queries for better semantic retrieval.

4. Run the retrieval test cell to verify the tool is found when you search for "look up details for a specific research paper".

    > **Try it:** Change the query to "find the authors of this paper" or "get metadata for arXiv 1706.03762" and see if the tool is still retrieved. This is semantic retrieval in action.

## Lab 2 Recap

| What You Built | Why It Matters |
|---------------|----------------|
| Vector search with 300 arXiv papers | Semantic retrieval foundation for the entire agent |
| 7 memory tables (2 SQL + 5 vector-enabled) | Each memory type serves a distinct cognitive function |
| MemoryManager with unified read/write | Clean interface hiding SQL and vector complexity |
| Thread-based conversational memory | Independent history per research session |
| Semantic Toolbox with LLM augmentation | Scale to hundreds of tools, LLM only sees relevant ones |

**Key Insight:** The `summary_id` column in conversational memory enables **log compaction** — a pattern borrowed from databases where old entries are compressed but not lost. Messages are *marked* as summarized, not deleted, preserving full audit history.

**Next up:** In Lab 3, you'll build the context engineering layer — usage tracking, summarization, just-in-time retrieval — and integrate Tavily for web search.

## Learn More

* [LangChain OracleVS Documentation](https://github.com/oracle/langchain-oracle)
* [HuggingFace sentence-transformers](https://huggingface.co/sentence-transformers/paraphrase-mpnet-base-v2)
* [HNSW Algorithm Explained](https://arxiv.org/abs/1603.09320)

## Acknowledgements

* **Author(s)** - Richmond Alake
* **Contributors** - Eli Schilling
* **Last Updated By/Date** - Published February, 2026
