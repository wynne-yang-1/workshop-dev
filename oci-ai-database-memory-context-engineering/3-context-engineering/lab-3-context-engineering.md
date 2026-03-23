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

### Background

#### What is Context Engineering?

> **Context engineering** refers to the set of strategies for curating and maintaining the optimal set of tokens (information) during LLM inference, including all the other information that may land there outside of the prompts.

This includes monitoring usage, compressing information, and providing just-in-time access to details when the agent needs them. It represents a broader shift from **prompt engineering** (crafting a single message) to **system design** (managing the entire lifecycle of data entering and exiting the context window).

#### What This Lab Covers

| Task | Function | Purpose |
|------|----------|---------|
| **1. Calculate Usage** | `calculate_context_usage()` | Monitor what % of the context window is used |
| **2. Summarize** | `summarise_context_window()` | Compress long content into summaries using LLM |
| **3. Compact** | `summarize_conversation()` / `summarize_and_store()` | Agent-triggered compaction when context gets long |
| **4. Just-in-Time Retrieval** | `expand_summary()` tool | Let Proteus expand summaries on demand |
| **5. Web Search** | `search_tavily()` tool | External retrieval with automatic knowledge base persistence |

#### The Context Management Flow

```
Context built → Check usage % → Proteus may compact (summarize) → Store summary with ID
                                                                ↓
Proteus sees: [Summary ID: abc123] Brief description ← Proteus calls expand_summary("abc123") if needed
```

This approach keeps the context lean while giving Proteus access to full details when required.

#### Just-in-Time (JIT) Retrieval

**Just-In-Time retrieval** is the process of fetching only the information needed at the exact moment the agent requires it, based on the current task or reasoning step. Instead of loading everything upfront, the system dynamically retrieves the minimal, most relevant data on demand.

In the context of agent memory, JIT is a retrieval-control strategy where memory access is triggered by the agent's current goal. Rather than preloading large histories or the full knowledge base, the system dynamically filters, ranks, and injects only the information that materially influences the next token. This reduces context saturation, improves attention allocation, and increases reasoning fidelity.

For Proteus, this means summary pointers (ID + description) are always loaded — cheap, a few tokens each. Full summary content is only retrieved when Proteus decides it's relevant to the current research query, avoiding thousands of wasted context tokens on summaries of unrelated sessions.

#### Design Decision: Mark Instead of Delete

When conversation history grows large, we need to reduce context. We chose to **mark messages as summarized** rather than delete them:

| Approach | Pros | Cons |
|----------|------|------|
| **Delete summarized messages** | Simple, immediate space savings | Permanent data loss, can't audit or recover |
| **Mark as summarized (our choice)** | Preserves history, reversible, auditable | Slightly more complex queries |

Memory should be *compressed* or *forgotten*, not *erased*. The original messages remain for auditing, debugging, or reprocessing. This is a form of **log compaction** — a pattern borrowed from databases and message queues where old entries are compressed but not lost.

#### The Search-and-Store Pattern

When Proteus calls `search_tavily()`, it doesn't just return results — it **persists them to the knowledge base**:

```
Proteus calls search_tavily("recent advances in diffusion models 2026")
       ↓
Tavily API returns results
       ↓
Each result is written to knowledge_base_vs with metadata (title, URL, timestamp)
       ↓
Future sessions can retrieve this information without searching again
```

This means Proteus **builds institutional knowledge over time**. Information discovered once becomes part of the agent's long-term memory, available for future conversations without additional API calls.

## Task 1: Restore State from Lab 2

The first cells in the notebook restore your credentials from `%store`, reconnect to the database, and rebuild the MemoryManager and Toolbox instances.

1. Run the credential restoration cell. You'll be prompted for your OpenAI API key.

2. Run the state rebuild cell. You should see a successful connection and "State rebuilt" confirmation.

    > **Why rebuild?** Each notebook runs in a fresh Python kernel. The `proteus` modules make this fast — `connect_to_oracle()`, `create_all_vector_stores()`, and the MemoryManager constructor take just a few seconds. The tables and data you created in Lab 2 are already in the database.

## Task 2: Context Window Usage Calculator

<details><summary>🔍 View source: <code>proteus/context.py</code> — Context window management utilities</summary>

```python
"""
Proteus Context Engineering
============================
Context window management utilities: usage calculation,
LLM-powered summarisation, and threshold-based offloading.
"""

import uuid

from proteus import config


def calculate_context_usage(context: str, model: str = None) -> dict:
    """Calculate context window usage as percentage."""
    model = model or config.OPENAI_MODEL
    estimated_tokens = len(context) // 4  # ~4 chars per token
    max_tokens = config.MODEL_TOKEN_LIMITS.get(model, 128000)
    percentage = (estimated_tokens / max_tokens) * 100
    return {
        "tokens": estimated_tokens,
        "max": max_tokens,
        "percent": round(percentage, 1),
    }


def summarise_context_window(
    content: str, memory_manager, llm_client, model: str = None
) -> dict:
    """Summarise context window using LLM and store in summary memory."""
    model = model or config.OPENAI_MODEL

    summary_prompt = f"""
You are compressing an AI research assistant's context window for later retrieval.
The content may include conversation memory, research papers, entities, workflows, and prior summaries.

Produce a compact summary that preserves:
- user's research goal and constraints
- key findings already established
- important entities (paper titles, author names, arXiv IDs, research topics)
- unresolved questions and next actions

Output 4-7 short bullet points.
Be faithful to the source, and do not add new facts.

Context window content:
{content[:3000]}
""".strip()

    response = llm_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": summary_prompt}],
        max_completion_tokens=220,
    )
    summary = response.choices[0].message.content

    desc_response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"Write a short label (max 12 words) for this summary:\n{summary}",
            }
        ],
        max_completion_tokens=40,
    )
    description = desc_response.choices[0].message.content.strip()

    summary_id = str(uuid.uuid4())[:8]
    memory_manager.write_summary(summary_id, content, summary, description)

    return {"id": summary_id, "description": description, "summary": summary}


def offload_to_summary(
    context: str,
    memory_manager,
    llm_client,
    threshold_percent: float = 80.0,
) -> tuple:
    """If context exceeds threshold, summarise and return compacted version."""
    usage = calculate_context_usage(context)

    if usage["percent"] < threshold_percent:
        return context, []  # No offload needed

    result = summarise_context_window(context, memory_manager, llm_client)

    compact = f"[Summary ID: {result['id']}] {result['description']}"
    return compact, [result]

```

**What this code does:** `calculate_context_usage()` estimates token count at ~4 characters per token and compares against the model's known limit from `config.MODEL_TOKEN_LIMITS`. `summarise_context_window()` sends context (up to 3,000 chars) to the LLM with a compression prompt, stores the result in Summary Memory, and returns the summary ID + description. `offload_to_summary()` combines both — if usage exceeds a threshold (default 80%), it automatically summarizes and returns a compact reference instead of the full content.

</details>


1. Run the cell that tests `calculate_context_usage()` with a sample string.

    > **Key concept:** The calculator estimates tokens at ~4 characters per token and compares against the model's known limit. When usage exceeds 80%, Proteus can trigger summarization to reclaim space.

## Task 3: Context Summarizer

1. Run the cell that calls `summarise_context_window()` on a knowledge base query result.

2. Observe the output: a summary ID, a short description, and the compressed bullet points.

    > **What's happening:** The LLM reads up to 3,000 characters of context, produces a 4-7 bullet summary preserving key facts and entities, then generates a 12-word label. The full content and summary are stored in Summary Memory — the context window only needs the ID and label.

## Task 4: Register Agent Tools

<details><summary>🔍 View source: <code>proteus/tools.py</code> — Agent-callable tools: summary, search, paper lookup</summary>

```python
"""
Proteus Tools
=============
Agent-callable tools: summary expansion/compaction, web search (Tavily),
and paper lookup. These are registered into the Toolbox at init time.

NOTE: Tools reference module-level singletons (memory_manager, toolbox, etc.)
that are set by init_tools() before use.
"""

import os
from datetime import datetime

from proteus.context import summarise_context_window

# ── Module-level references (set by init_tools) ──────────
_memory_manager = None
_toolbox = None
_llm_client = None
_tavily_client = None


def init_tools(memory_manager, toolbox, llm_client, tavily_api_key: str = None):
    """
    Initialise module-level references and register all tools into the toolbox.

    Call this once after creating the MemoryManager, Toolbox, and OpenAI client.
    """
    global _memory_manager, _toolbox, _llm_client, _tavily_client

    _memory_manager = memory_manager
    _toolbox = toolbox
    _llm_client = llm_client

    # ── Tavily (optional) ─────────────────────────────────
    tavily_key = tavily_api_key or os.environ.get("TAVILY_API_KEY", "")
    if tavily_key:
        try:
            from tavily import TavilyClient
            _tavily_client = TavilyClient(api_key=tavily_key)
        except ImportError:
            print("⚠️ tavily-python not installed — search_tavily will be unavailable.")
            _tavily_client = None
    else:
        _tavily_client = None

    # ── Register tools ────────────────────────────────────
    toolbox.register_tool(expand_summary, augment=True)
    toolbox.register_tool(summarize_and_store, augment=True)
    toolbox.register_tool(summarize_conversation, augment=True)
    toolbox.register_tool(lookup_paper_details, augment=True)

    if _tavily_client:
        toolbox.register_tool(search_tavily, augment=True)
        print("✅ Registered 5 tools (including search_tavily)")
    else:
        print("✅ Registered 4 tools (search_tavily skipped — no Tavily API key)")
        print("   💡 To enable web search, set TAVILY_API_KEY in your environment.")
        print("   💡 Alternative: install duckduckgo-search and adapt search_tavily().")


# ── Summary tools ─────────────────────────────────────────

def expand_summary(summary_id: str) -> str:
    """Expand a summary reference to full content, including the original conversation
    messages that were compacted into it. Use when you need more details from a
    [Summary ID: xxx] reference."""
    summary_text = _memory_manager.read_summary_memory(summary_id)

    original_msgs = _memory_manager.get_messages_by_summary_id(summary_id)
    if original_msgs:
        lines = [f"[{m['role']}] {m['content']}" for m in original_msgs]
        return (
            f"Summary:\n{summary_text}\n\n"
            f"Original messages ({len(original_msgs)}):\n" + "\n".join(lines)
        )
    return summary_text


def summarize_and_store(text: str) -> str:
    """Summarize a long text block and store it. Returns [Summary ID: ...] for later expansion."""
    result = summarise_context_window(text, _memory_manager, _llm_client)
    return f"Stored as [Summary ID: {result['id']}] {result['description']}"


def summarize_conversation(thread_id: str) -> str:
    """
    Summarize unsummarized conversation turns for a research session thread and mark those
    turns with a summary_id. Use this when conversation memory becomes long and
    you need context compaction.
    """
    unsummarized = _memory_manager.get_unsummarized_messages(thread_id, limit=200)
    if not unsummarized:
        return "No unsummarized conversation turns found."

    full_text = "\n".join([f"[{m['role']}] {m['content']}" for m in unsummarized])
    result = summarise_context_window(full_text, _memory_manager, _llm_client)

    message_ids = [m["id"] for m in unsummarized]
    _memory_manager.mark_as_summarized(thread_id, result["id"], message_ids=message_ids)

    return f"Conversation summarized as [Summary ID: {result['id']}] {result['description']}"


# ── Research tools ────────────────────────────────────────

def lookup_paper_details(arxiv_id: str) -> str:
    """Look up detailed metadata for a research paper by its arXiv ID."""
    # In production, this would call the arXiv API
    mock_papers = {
        "1706.03762": "Title: Attention Is All You Need | Authors: Vaswani et al. | Subject: cs.CL | Year: 2017",
        "2005.14165": "Title: Language Models are Few-Shot Learners | Authors: Brown et al. | Subject: cs.CL | Year: 2020",
        "2303.08774": "Title: GPT-4 Technical Report | Authors: OpenAI | Subject: cs.CL | Year: 2023",
    }
    return mock_papers.get(arxiv_id, f"❓ Paper not found: {arxiv_id}")


# ── Web search ────────────────────────────────────────────

def search_tavily(query: str, max_results: int = 5):
    """
    Search the web for information not available in the internal knowledge base.
    Results are automatically stored in the knowledge base for future reference.
    Use for recent papers, new research findings, and unfamiliar techniques.
    """
    if _tavily_client is None:
        return "Error: Tavily client not configured. Set TAVILY_API_KEY."

    response = _tavily_client.search(query=query, max_results=max_results)
    results = response.get("results", [])

    for result in results:
        text = (
            f"Title: {result.get('title', '')}\n"
            f"Content: {result.get('content', '')}\n"
            f"URL: {result.get('url', '')}"
        )
        metadata = {
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "score": result.get("score", 0),
            "source_type": "tavily_search",
            "query": query,
            "timestamp": datetime.now().isoformat(),
        }
        _memory_manager.write_knowledge_base(text, metadata)

    return results

```

**What this code does:** `init_tools()` is the one-call setup function that wires up module-level references and registers all tools into the Toolbox. It registers five tools: `expand_summary()` retrieves full content from a Summary ID; `summarize_and_store()` compresses any text and stores it; `summarize_conversation()` compacts a thread's chat history using the mark-not-delete pattern; `lookup_paper_details()` provides mock arXiv paper metadata; and `search_tavily()` searches the web and automatically persists results to the knowledge base. If no Tavily API key is provided, web search is skipped gracefully.

</details>


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
