# Lab 3: Context Engineering & Web Search

## Introduction

While memory engineering focuses on *what to store and retrieve*, context engineering focuses on *how to manage what's in the context window right now*. In this lab you'll use the context utilities from the `proteus` package to monitor token usage, compress information with LLM-powered summarization, and integrate web search so Proteus can find information beyond the internal knowledge base.

By the end of this lab, Proteus will have a full suite of agent-callable tools — summary expansion, conversation compaction, and web search — all registered in the semantic Toolbox for on-demand retrieval.

**Estimated Time:** 15 minutes

### Objectives

In this lab you will:

1. Rebuild state from Lab 2 (connection, MemoryManager, Toolbox)
2. Test context window usage calculation
3. Summarize content and store it in Summary Memory
4. Register agent-callable tools for summarization, expansion, and web search
5. Test the search-and-store pattern with Tavily

### Prerequisites

This lab assumes you have:

* Completed Lab 2 (memory tables created, knowledge base seeded, MemoryManager initialized)
* An OpenAI API key
* A Tavily API key (optional — web search will be skipped if unavailable)
* Opened `notebooks/lab-3-context-engineering.ipynb` in VS Code

## Task 1: Restore State from Lab 2

The first cells in the notebook restore your credentials from `%store`, reconnect to the database, and rebuild the MemoryManager and Toolbox instances.

1. Run the credential restoration cell. You'll be prompted for your OpenAI API key.

2. Run the state rebuild cell. You should see a successful connection and "State rebuilt" confirmation.

    > **Why rebuild?** Each notebook runs in a fresh Python kernel. The `proteus` modules make this fast — `connect_to_oracle()`, `create_all_vector_stores()`, and the MemoryManager constructor take just a few seconds. The tables and data you created in Lab 2 are already in the database.

## Task 2: Context Window Usage Calculator

1. Run the cell that tests `calculate_context_usage()` with a sample string.

    > **Key concept:** The calculator estimates tokens at ~4 characters per token and compares against the model's known limit. When usage exceeds 80%, Proteus can trigger summarization to reclaim space.

## Task 3: Context Summarizer

1. Run the cell that calls `summarise_context_window()` on a knowledge base query result.

2. Observe the output: a summary ID, a short description, and the compressed bullet points.

    > **What's happening:** The LLM reads up to 3,000 characters of context, produces a 4-7 bullet summary preserving key facts and entities, then generates a 12-word label. The full content and summary are stored in Summary Memory — the context window only needs the ID and label.

## Task 4: Register Agent Tools

1. Run the cell that prompts for your **Tavily API key**. Press Enter to skip if you don't have one — the workshop will continue without web search.

    > **💡 Alternative to Tavily:** If your environment can't reach the Tavily API, you can install the `duckduckgo-search` package and adapt the `search_tavily()` function in `proteus/tools.py` to use DuckDuckGo instead. The search-and-store pattern works the same way regardless of the search backend.

2. Run the cell that calls `init_tools()`. This registers five tools (or four if Tavily is skipped):

    | Tool | Purpose |
    |------|---------|
    | `expand_summary` | Retrieve full content from a Summary ID reference |
    | `summarize_and_store` | Compress any text block and store it |
    | `summarize_conversation` | Compact a conversation thread's history |
    | `lookup_paper_details` | Look up paper metadata by arXiv ID |
    | `search_tavily` | Search the web and persist results to knowledge base |

## Task 5: Test Tool Retrieval

1. Run the two retrieval test cells. The first searches for "Search the internet for recent research papers" — it should find `search_tavily` (if registered). The second searches for "compact the conversation context" — it should find summary tools.

    > **Key concept:** Proteus doesn't get all tools at every turn. The Toolbox uses semantic retrieval to find the 3-5 most relevant tools for each query. This keeps the context lean and improves tool selection accuracy.

## Task 6: Test the Search-and-Store Pattern

1. If Tavily is configured, run the cell that calls `search_tavily("recent advances in AI agent memory 2026")`.

2. Observe: the function returns web search results AND automatically writes each result to the knowledge base vector store with metadata (title, URL, timestamp, source type).

3. The verification query shows the newly stored results are immediately searchable in the knowledge base.

    > **Key insight:** This search-and-store pattern means Proteus **builds institutional knowledge over time**. The first time an analyst asks about a topic, Proteus searches externally. The second time, Proteus finds the answer in its own knowledge base — no external call needed, faster and cheaper.

## Lab 3 Recap

| What You Built | Why It Matters |
|---------------|----------------|
| `calculate_context_usage()` | Monitor context consumption and trigger compaction proactively |
| `summarise_context_window()` | LLM-powered compression that preserves key research details |
| `offload_to_summary()` | Automatic threshold-based context offloading |
| `expand_summary()` tool | JIT retrieval — Proteus expands only the summaries it needs |
| `summarize_conversation()` tool | Log compaction for long research session threads |
| `search_tavily()` tool | External search with automatic knowledge base persistence |

**Key Insight:** The combination of just-in-time retrieval and the search-and-store pattern creates a virtuous cycle. Summary pointers stay cheap (a few tokens each), full content is retrieved only when needed, and every external search enriches the knowledge base for future sessions.

**Next up:** In Lab 4, you'll wire everything together into the `call_agent` harness, run Proteus through real research scenarios, compare the engineered approach against a naive baseline, and launch a live chat UI.

## Learn More

* [Tavily AI Search API](https://tavily.com/)
* [Context Window Management Best Practices](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)

## Acknowledgements

* **Author(s)** - Richmond Alake
* **Contributors** - Eli Schilling
* **Last Updated By/Date** - Published February, 2026
