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
