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

## Task 1: Restore Credentials and Connect

The first cell restores the credentials you saved in Lab 1 using `%store -r` and sets them as environment variables so the `proteus` modules can access them.

1. Run the first two code cells to restore credentials and establish the database connection.

2. You should see a successful connection message with the Oracle version banner.

    > **What's happening:** The `proteus.db.connect_to_oracle()` function uses the `oracledb` thin driver with retry logic. It reads credentials from `os.environ`, which we just populated from the `%store` values.

## Task 2: Initialize Embeddings and Create a Vector Search Demo Table

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

1. Run the cell that creates the `MemoryManager` instance, passing it the database connection, conversation table name, and all five vector stores.

2. Run the **smoke test** cells to verify:
    - Writing and reading conversational memory (thread-based chat history)
    - Searching the knowledge base with a natural language query

    > **Key concept:** The MemoryManager provides a unified read/write interface across all seven memory types. Each `read_*` method returns formatted text ready for the LLM context window, with purpose headers that guide the agent's behavior.

## Task 9: Initialize the Toolbox and Register a Test Tool

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
