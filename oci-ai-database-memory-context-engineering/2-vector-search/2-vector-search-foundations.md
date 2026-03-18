# Lab 2: Vector Search Foundations

## Introduction

Using Oracle AI Database 26ai and LangChain OracleVS

**Estimated Time:** 15 minutes

### Objectives

In this lab, you'll learn how to store and search documents using **semantic similarity** — finding results based on meaning rather than exact keyword matches. This is the foundation that powers every memory type we'll build in later activities.

You'll work with **SeerGroup's research paper collection**: a curated set of academic papers spanning AI, physics, mathematics, and more. Our AI research assistant "Proteus" will use this collection to help analysts navigate the flood of academic literature.

### What You'll Learn


| Task | Description |
|------|-------------|
| **1. Initialize Embeddings** | Load a HuggingFace embedding model to convert text into vectors |
| **2. Create Vector-Enabled Table** | Set up an Oracle-backed vector store with cosine distance via `OracleVS` |
| **3. Create Index** | Build an HNSW (Hierarchical Navigable Small World) index for fast similarity search |
| **4. Add Documents** | Store research papers from the arXiv dataset with metadata |
| **5. Query** | Search for similar documents using natural language |
| **6. Filter Results** | Use metadata filters to narrow down search results |

### Key Components

- **`OracleVS`**: LangChain abstraction over Oracle vector-enabled SQL tables
- **`HuggingFaceEmbeddings`**: Converts text to 768-dimensional vectors
- **`DistanceStrategy.COSINE`**: Measures vector similarity using cosine distance
- **HNSW Index**: Graph-based ANN index for fast and accurate nearest-neighbor retrieval

## Task 0: Choose Your Own Adventure

To simplify and accelerate this workshop, we've created a pre-built notebook with all the code. You may [download it here](https://raw.githubusercontent.com/enschilling/workshop-dev/refs/heads/main/oci-ai-database-memory-context-engineering/files/workshop-complete.ipynb) if you'd like.

<details><summary>Choose the path of least resistance</summary>

1. Download and save the complete workshop `.ipynb` notebook, then open it in the same VS Code instance that you used for lab 1. Ensure you select the same kernel: **`oracle-agent-env`**.

2. Follow along in the lab guide as you execute each code block to learn more about all the components being constructed.

3. Enjoy!

</details>

<details><summary>Off the beaten path - build your own notebook</summary>

1. This path takes a bit of a turn as you forge your way through the copy&paste jungle. However, you may find yourself drawing a bit closer to the code as you inspect it more closely during the journey.

2. Create a new `.ipynb` in your existing VS Code instance (don't close the other one): `ctrl+shift+p` (windows) or `cmd+shift+p` (Mac).

3. As you progress through the lab instructions, you'll copy each code snippet from the guide, and paste / run in a new code block in your Jupyter notebook.

4. Labs 2-6 will all be run in a single notebook.

5. That's it! Enjoy, have fun, and we'll see you on the other side.

</details>

## Task 1: Connect to Oracle AI Database

Your environment has been pre-configured with Oracle AI Database 26ai running locally. The `VECTOR` user and connection details are ready to use.

    ```
    import oracledb
    import time
    import logging

    %store -r adb_dsn vector_user vector_password

    def connect_to_oracle(
        max_retries=3,
        retry_delay=5,
        user=vector_user,
        password=vector_password,
        dsn=adb_dsn,
        program="seergroup.proteus.workshop",
    ):
        """
        Connect to Oracle database with retry logic and helpful error messages.
        """
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Connection attempt {attempt}/{max_retries}...")
                conn = oracledb.connect(
                    user=user, password=password, dsn=dsn, program=program
                )
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

    vector_conn = connect_to_oracle()
    print("Using user:", vector_conn.username)
    ```
    
## Task 2: Initialize Embeddings and Create a Vector-Enabled Table

We'll use the `sentence-transformers/paraphrase-mpnet-base-v2` model to convert text into 768-dimensional vectors. OracleVS handles the table creation, embedding storage, and similarity search under the hood.

    ```python
    <copy>
    from langchain_oracledb.vectorstores import OracleVS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_oracledb.vectorstores.oraclevs import create_index
    from langchain_community.vectorstores.utils import DistanceStrategy

    # Suppress verbose logging from langchain_oracledb
    logging.getLogger("langchain_oracledb").setLevel(logging.CRITICAL)

    # Initialize the embedding model
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-mpnet-base-v2"
    )

    # Create the vector-enabled SQL table via OracleVS
    vector_store = OracleVS(
        client=vector_conn,
        embedding_function=embedding_model,
        table_name="VECTOR_SEARCH_DEMO",
        distance_strategy=DistanceStrategy.COSINE,
    )
    </copy>
    ```

### Create an HNSW Index

HNSW (Hierarchical Navigable Small World) is a graph-based approximate nearest-neighbor index. It provides fast, accurate similarity search at scale — essential when your knowledge base grows to thousands or millions of documents.

    ```python
    def safe_create_index(conn, vs, idx_name):
        """Create index, skipping if it already exists."""
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


    safe_create_index(vector_conn, vector_store, "oravs_hnsw")
    ```

--------

## Task 3: Ingest Research Papers

In a real deployment, this data would come from institutional repositories, journal APIs, or preprint servers. Here we'll load papers from the `nick007x/arxiv-papers` dataset on HuggingFace — a collection of arXiv papers spanning multiple disciplines that Proteus will use to answer research queries.

    ```
    from datasets import load_dataset

    MAX_PAPERS = 300
    ds_stream = load_dataset("nick007x/arxiv-papers", split="train", streaming=True)

    sampled_papers = []
    texts = []
    metadata_list = []

    for i, item in enumerate(ds_stream):
        if i >= MAX_PAPERS:
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
    print(f"✅ Ingested {len(texts)} research papers into VECTOR_SEARCH_DEMO")
    ```

> **🔍 Notice** The process to ingest the data may take 3-5 minutes. Your patience is appreciated.

    ```
    # Inspect one sample to see the metadata fields we can filter on
    sample_primary_subject = sampled_papers[0]["primary_subject"] if sampled_papers else ""
    sample_arxiv_id = sampled_papers[0]["arxiv_id"] if sampled_papers else ""
    print("Sample primary subject:", sample_primary_subject)
    print("Sample arxiv_id:", sample_arxiv_id)
    ```

## Task 4: Querying with Natural Language

Now let's see the power of semantic search. Unlike keyword search, vector similarity finds documents based on *meaning*. A query about "how neural networks learn representations" will match papers about deep learning, feature extraction, and representation learning — even if those exact words don't appear in the query.

### Basic Similarity Search

    ```
    query = "Find research papers about planetary exploration mission planning"

    results = vector_store.similarity_search(query, k=3)

    for i, doc in enumerate(results, start=1):
        print(f"--- Result {i} ---")
        print("Title:", doc.metadata.get("title", "N/A"))
        print("Subject:", doc.metadata.get("primary_subject", "N/A"))
        print("Text:", doc.page_content[:200], "...")
        print()
    ```

> **🔍 Notice** how the search returns relevant papers even when the query uses different terminology than the paper titles. That's semantic similarity at work — the embedding model understands the *meaning* behind the words.

### Search with Relevance Scores

Scores let Proteus gauge confidence. A score close to 0 means high similarity (cosine distance); a score near 1 means low relevance.

    ```
    query = "methods for detecting gravitational waves"

    results = vector_store.similarity_search_with_score(query, k=3)

    for doc, score in results:
        print(f"Score: {score:.4f}")
        print(f"Title: {doc.metadata.get('title', 'N/A')}")
        print(f"Subject: {doc.metadata.get('primary_subject', 'N/A')}")
        print("------")
    ```

## Task 5: Filtered Search with Metadata

In a real research workflow, Proteus needs to narrow results by subject area, specific paper IDs, or authors. OracleVS supports metadata filters that combine with vector similarity.

### Filter by Subject Area

    ```
    query = "Find papers related to mission planning and observational astronomy"

    docs = vector_store.similarity_search(
        query,
        k=3,
        filter={"primary_subject": {"$eq": sample_primary_subject}},
    )

    for doc in docs:
        print("Title:", doc.metadata.get("title", "N/A"))
        print("Subject:", doc.metadata.get("primary_subject", "N/A"))
        print("Text:", doc.page_content[:150], "...")
        print("------")
    ```

### Filter by Paper ID

    ```
    docs = vector_store.similarity_search(
        query="Explain key themes in this research paper",
        k=5,
        filter={"id": {"$in": [sample_arxiv_id]}},
    )

    for doc in docs:
        print("Title:", doc.metadata.get("title", "N/A"))
        print("ArXiv ID:", doc.metadata.get("arxiv_id", "N/A"))
        print("------")
    ```

## Lab 2 Recap

You've now built the search foundation that Proteus will rely on:

| What You Did | Why It Matters |
|-------------|----------------|
| Created a vector-enabled SQL table | Documents stored with embeddings for semantic retrieval |
| Built an HNSW index | Fast approximate nearest-neighbor search at scale |
| Ingested 1,000 arXiv research papers | Real academic data with rich metadata (subject, authors, IDs) |
| Queried with natural language | "Planetary exploration" finds relevant papers without keyword matching |
| Applied metadata filters | Narrow results by subject area or specific paper IDs |

**Next up**: In Lab 3, we'll design the complete memory architecture that gives Proteus seven distinct types of memory — each with a specific purpose and storage strategy.

## Learn More



## Acknowledgements

- **Author** - Richmond Alake
- **Contributors** - Eli Schilling
- **Last Updated By/Date** - Published February, 2026