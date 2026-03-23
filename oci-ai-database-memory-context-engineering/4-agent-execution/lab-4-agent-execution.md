# Lab 4: Agent Execution & Evaluation

## Introduction

This is where everything comes together. You'll initialize the full agent harness from `proteus.agent`, run Proteus through multi-turn research scenarios that test memory continuity and context management, then compare the engineered approach against a naive baseline that lacks memory and context engineering. Finally, you'll launch a Streamlit chat UI and interact with Proteus in a browser.

The agent harness implements the turn-level loop pattern: build context from memory, retrieve relevant tools, call the LLM, execute tool calls, persist results, repeat. Every component you built in Labs 2 and 3 is now imported and orchestrated by `call_agent()`.

**Estimated Time:** 20 minutes

### Objectives

In this lab you will:

1. Initialize the complete agent stack (MemoryManager + Toolbox + tools + agent harness)
2. Run Proteus through four progressive research scenarios
3. Visualize context window growth across agent iterations
4. Run a naive baseline agent and compare context growth head-to-head
5. Launch the Streamlit chat UI and interact with Proteus in a browser

### Prerequisites

This lab assumes you have:

* Completed Labs 2 and 3 (memory tables created, knowledge base seeded, tools registered)
* An OpenAI API key
* Opened `notebooks/lab-4-agent-execution.ipynb` in VS Code

### Background

#### The Turn-Level Agent Run

Each call to `call_agent()` represents one **agent run** — one user turn handled end-to-end. Within a run, the **tool-call loop** repeats: model reasoning → optional tool calls → harness executes tools → model observes results → repeat until a final answer.

An **agent harness** is the runtime scaffolding around that loop. In this workshop, it is a **memory-based agent harness** where context is assembled from multiple memory types each run, tools are discovered and executed within the run, outputs are written back into memory for future runs, and summaries compact context while preserving continuity.

#### The Agent Flow

```
1. BUILD CONTEXT (programmatic)
   ├── Read conversational memory (unsummarized turns only)
   ├── Read knowledge base (relevant research papers)
   ├── Read workflow memory (past search-and-analysis patterns)
   ├── Read entity memory (papers, authors, topics)
   └── Read summary context (available summary IDs + descriptions)

2. GET TOOLS (programmatic)
   └── Retrieve semantically relevant tools from toolbox

3. STORE USER MESSAGE (programmatic)
   └── Persist the user message + best-effort entity extraction

4. WITHIN-RUN TOOL-CALL LOOP (up to max_iterations, within time budget)
   ├── Call LLM with context + tool schemas
   ├── If tool calls → execute tools and append results
   ├── If tools changed memory (search/compaction) → rebuild context
   └── If no tool calls → finalize answer

5. GUARDED STOP
   └── If budget hit → force a final best-effort answer (no tools)

6. SAVE RESULTS (programmatic)
   ├── Write workflow (if tools were used)
   ├── Best-effort entity extraction on final answer
   └── Store assistant response in conversational memory
```

#### The System Prompt

The system prompt tells Proteus how to use its memory systems and tools. It establishes a **priority order** for memory types — this is critical for reliable behavior:

1. **Conversation Memory** — check what the user already asked and what you already answered
2. **Knowledge Base Memory** — cite facts from stored papers and search results before searching externally
3. **Entity Memory** — resolve named references ("that author", "the paper we discussed")
4. **Workflow Memory** — reuse proven search-and-analysis sequences for similar past queries
5. **Summary Memory** — expand a summary ID only when specific details from an older session are needed

#### Why the Naive Baseline Matters

The naive agent (`call_agent_naive`) deliberately removes tool output offloading, summarization tools, context refresh after search, and memory-backed context rebuild. This creates unbounded context growth — after just 3 web searches, the context can grow by 10,000+ tokens, consuming budget that could be used for reasoning. The head-to-head comparison makes the impact of memory and context engineering concrete and measurable.

## Task 1: Initialize the Agent

<details><summary>🔍 View source: <code>proteus/agent.py</code> — System prompt, agent harness, and naive baseline</summary>

```python
"""
Proteus Agent
=============
Turn-level agent harness with memory-backed context assembly,
semantic tool retrieval, and tool-call loop.
Also includes the naive baseline agent for comparison.
"""

import json as json_lib
import time

from openai import OpenAI

from proteus import config
from proteus.context import calculate_context_usage

# ── Module-level singletons (set by init_agent) ──────────
_memory_manager = None
_toolbox = None
_client = None

# Persistent trackers
context_size_history = []           # (run_label, iteration, estimated_tokens)
naive_context_size_history = []     # flat list of estimated_tokens
_naive_messages_by_thread = {}


AGENT_SYSTEM_PROMPT = """
# System Instructions
You are Proteus, SeerGroup's AI Research Assistant. You have access to memory systems and
research tools to help analysts navigate academic literature, synthesize findings, and track
research threads across sessions.

IMPORTANT: The user's input contains CONTEXT retrieved from multiple memory systems.
Each memory section has a Purpose and When-to-use guide — follow them.

## Memory Priority Order
1. **Conversation Memory** — check what the user already asked and what you already answered.
2. **Knowledge Base Memory** — cite facts from stored papers, abstracts, and web search results
   before searching externally.
3. **Entity Memory** — resolve named references ("that author", "the paper we discussed") from here.
4. **Workflow Memory** — reuse proven search-and-analysis sequences for similar past queries.
5. **Summary Memory** — expand a summary ID only when you need specific details from an older session.

## Tool Output Handling
Tool call outputs are logged to a Tool Log table and replaced with compact references in context.
The preview in each [Tool Log ...] reference contains enough to reason about the result.
If you need the full output, it can be retrieved from the database — but prefer working with
the preview and the knowledge base (where search results are also stored).

## Context Management
If conversation memory is getting long or repetitive, call summarize_conversation(thread_id)
to compact it. Use summarization tools at your discretion when they improve context quality.

When answering:
1. FIRST, use the context provided in the input
2. Expand summary IDs just-in-time when needed
3. Use external search tools only if memory context is insufficient
4. Keep responses evidence-based and grounded in the retrieved research context
5. Cite paper titles, authors, and arXiv IDs when available
"""


def init_agent(memory_manager, toolbox, openai_client=None):
    """Initialise module-level references. Call once at startup."""
    global _memory_manager, _toolbox, _client
    _memory_manager = memory_manager
    _toolbox = toolbox
    _client = openai_client or OpenAI()


def execute_tool(tool_name: str, tool_args: dict) -> str:
    """Execute a tool by looking it up in the toolbox."""
    if tool_name not in _toolbox._tools_by_name:
        return f"Error: Tool '{tool_name}' not found"
    return str(_toolbox._tools_by_name[tool_name](**tool_args) or "Done")


def call_openai_chat(messages: list, tools: list = None, model: str = None):
    """Call OpenAI Chat Completions API with tools."""
    model = model or config.OPENAI_MODEL
    kwargs = {"model": model, "messages": messages}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return _client.chat.completions.create(**kwargs)


# ══════════════════════════════════════════════════════════
# ENGINEERED AGENT
# ══════════════════════════════════════════════════════════

def call_agent(
    query: str,
    thread_id: str = "1",
    max_iterations: int = 10,
    max_execution_time_s: float = 60.0,
) -> str:
    """Turn-level agent harness: build context, run tool-call loop, persist results."""
    thread_id = str(thread_id)
    steps = []
    run_label = f"Run {len(set(r for r, _, _ in context_size_history)) + 1}"

    start_time = time.time()
    timed_out = False

    # ── 1. Build context from memory ──
    print("\n" + "=" * 50)
    print("🧠 BUILDING CONTEXT...")

    def build_context() -> str:
        ctx = f"# Research Query\n{query}\n\n"
        ctx += _memory_manager.read_conversational_memory(thread_id) + "\n\n"
        ctx += _memory_manager.read_knowledge_base(query) + "\n\n"
        ctx += _memory_manager.read_workflow(query) + "\n\n"
        ctx += _memory_manager.read_entity(query) + "\n\n"
        ctx += _memory_manager.read_summary_context(query) + "\n\n"
        return ctx

    context = build_context()

    print("==== CONTEXT WINDOW ====\n")
    print(context)

    # ── 2. Check context usage ──
    usage = calculate_context_usage(context)
    print(f"📊 Context: {usage['percent']}% ({usage['tokens']}/{usage['max']} tokens)")
    if usage["percent"] > 80:
        print("⚠️ Context >80% — Proteus may call summarize_conversation(thread_id) for compaction.")

    # ── 3. Get tools ──
    dynamic_tools = _memory_manager.read_toolbox(query, k=5)

    summary_tool_candidates = _memory_manager.read_toolbox(
        "summarize conversation compact context expand summary memory", k=5
    )
    must_have = {"expand_summary", "summarize_conversation", "summarize_and_store"}
    existing = {t.get("function", {}).get("name") for t in dynamic_tools}

    for tool in summary_tool_candidates:
        name = tool.get("function", {}).get("name")
        if name in must_have and name not in existing:
            dynamic_tools.append(tool)
            existing.add(name)

    print(f"🔧 Tools: {[t['function']['name'] for t in dynamic_tools]}")

    # ── 4. Store user message & extract entities ──
    _memory_manager.write_conversational_memory(query, "user", thread_id)
    try:
        _memory_manager.write_entity("", "", "", llm_client=_client, text=query)
    except Exception:
        pass

    # ── 5. Within-run tool-call loop ──
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]
    final_answer = ""

    tool_schema_tokens = len(json_lib.dumps(dynamic_tools)) // 4 if dynamic_tools else 0

    print("\n🤖 TOOL-CALL LOOP")
    for iteration in range(max_iterations):
        print(f"\n--- Iteration {iteration + 1} ---")

        total_chars = sum(len(m.get("content", "") or "") for m in messages)
        est_tokens = (total_chars // 4) + tool_schema_tokens
        context_size_history.append((run_label, iteration + 1, est_tokens))

        if max_execution_time_s is not None:
            elapsed = time.time() - start_time
            if elapsed > max_execution_time_s:
                timed_out = True
                print(f"\n⏱️ Time limit reached ({elapsed:.1f}s). Finalizing...")
                break

        response = call_openai_chat(messages, tools=dynamic_tools)
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                raw_args = tc.function.arguments or "{}"
                try:
                    tool_args = json_lib.loads(raw_args)
                except Exception as e:
                    result = f"Error: invalid JSON arguments for {tool_name}: {e}"
                    steps.append(f"{tool_name}(<invalid args>) → failed")
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                    continue

                if not isinstance(tool_args, dict):
                    result = f"Error: arguments for {tool_name} must be a JSON object."
                    steps.append(f"{tool_name}(<non-object args>) → failed")
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                    continue

                if tool_name == "summarize_conversation":
                    tool_args["thread_id"] = thread_id

                args_display = {
                    k: (v[:50] + "..." if isinstance(v, str) and len(v) > 50 else v)
                    for k, v in tool_args.items()
                }
                print(f"🛠️ {tool_name}({args_display})")

                if max_execution_time_s is not None:
                    elapsed = time.time() - start_time
                    if elapsed > max_execution_time_s:
                        timed_out = True
                        result = f"Error: time limit reached before executing {tool_name}."
                        steps.append(f"{tool_name}({args_display}) → timed out")
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                        break

                try:
                    result = execute_tool(tool_name, tool_args)
                    steps.append(f"{tool_name}({args_display}) → success")
                except Exception as e:
                    result = f"Error: {e}"
                    steps.append(f"{tool_name}({args_display}) → failed")

                print(f"   → {result[:200]}...")

                compact_result = _memory_manager.write_tool_log(
                    thread_id, tc.id, tool_name, raw_args, str(result)
                )
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": compact_result})

                if tool_name in {"search_tavily", "summarize_conversation", "summarize_and_store"}:
                    context = build_context()
                    if len(messages) >= 2 and messages[1].get("role") == "user":
                        messages[1]["content"] = context
                    usage = calculate_context_usage(context)
                    print(f"   Refreshed context: {usage['percent']}% ({usage['tokens']}/{usage['max']} tokens)")

            if timed_out:
                break
        else:
            final_answer = msg.content or ""
            print(f"\n✅ DONE ({len(steps)} tool calls)")
            break

    # ── Guarded stop ──
    if not final_answer:
        reason = "time limit" if timed_out else "iteration limit"
        print(f"\n⚠️ Stopped due to {reason}. Generating best-effort final answer...")
        try:
            final_messages = messages + [
                {"role": "user", "content": "Finalize your answer using context so far. Do not call tools."}
            ]
            final_resp = call_openai_chat(final_messages, tools=None)
            final_answer = final_resp.choices[0].message.content or ""
        except Exception as e:
            final_answer = f"Error: unable to finalize answer: {e}"

    # ── 6. Save results ──
    if steps:
        _memory_manager.write_workflow(query, steps, final_answer)
    try:
        _memory_manager.write_entity("", "", "", llm_client=_client, text=final_answer)
    except Exception:
        pass
    _memory_manager.write_conversational_memory(final_answer, "assistant", thread_id)

    print("\n" + "=" * 50 + f"\n💬 ANSWER:\n{final_answer}\n" + "=" * 50)
    return final_answer


# ══════════════════════════════════════════════════════════
# NAIVE BASELINE (no context engineering)
# ══════════════════════════════════════════════════════════

def call_agent_naive(
    query: str,
    thread_id: str = "naive_1",
    dynamic_tools_override: list = None,
    max_iterations: int = 10,
    max_execution_time_s: float = 60.0,
) -> str:
    """Naive agent harness — NO context engineering.

    Differences from call_agent:
    1. Full raw tool outputs stay in messages (no write_tool_log offloading)
    2. No summarisation tools available (agent cannot compact context)
    3. No context refresh after memory-mutating tools
    4. Messages persist across calls — context only grows, never shrinks
    5. No memory reads — conversation history IS the raw messages list
    """
    thread_id = str(thread_id)
    steps = []
    start_time = time.time()
    timed_out = False

    if dynamic_tools_override is not None:
        dynamic_tools = dynamic_tools_override
    else:
        dynamic_tools = _memory_manager.read_toolbox(query, k=5)
    dynamic_tools = [
        t for t in dynamic_tools
        if t.get("function", {}).get("name")
        not in {"summarize_conversation", "summarize_and_store", "expand_summary"}
    ]

    if thread_id not in _naive_messages_by_thread:
        _naive_messages_by_thread[thread_id] = [
            {"role": "system", "content": "You are a Research Paper Assistant with access to tools."}
        ]
    messages = _naive_messages_by_thread[thread_id]

    messages.append({"role": "user", "content": query})
    final_answer = ""

    tool_schema_chars = len(json_lib.dumps(dynamic_tools)) if dynamic_tools else 0
    tool_schema_tokens = tool_schema_chars // 4

    for iteration in range(max_iterations):
        msg_chars = sum(len(m.get("content", "") or "") for m in messages)
        naive_context_size_history.append((msg_chars // 4) + tool_schema_tokens)

        if max_execution_time_s and (time.time() - start_time) > max_execution_time_s:
            timed_out = True
            break

        response = call_openai_chat(messages, tools=dynamic_tools)
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                tool_args = json_lib.loads(tc.function.arguments or "{}")
                try:
                    result = execute_tool(tc.function.name, tool_args)
                    steps.append(f"{tc.function.name} → success")
                except Exception as e:
                    result = f"Error: {e}"
                    steps.append(f"{tc.function.name} → failed")

                messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
        else:
            final_answer = msg.content or ""
            break

    if not final_answer:
        try:
            messages.append({"role": "user", "content": "Finalize your answer. Do not call tools."})
            final_answer = call_openai_chat(messages, tools=None).choices[0].message.content or ""
        except Exception as e:
            final_answer = f"Error: {e}"

    messages.append({"role": "assistant", "content": final_answer})
    print(f"✅ Naive agent done ({len(steps)} tool calls, {len(messages)} messages in context)")
    return final_answer

```

**What this code does:** This is the largest module — it contains the complete agent runtime. `AGENT_SYSTEM_PROMPT` defines Proteus's persona, memory priority order, and tool output handling rules. `init_agent()` sets module-level references so `call_agent()` can access the MemoryManager and Toolbox. `call_agent()` is the turn-level harness: it builds context from all memory types, retrieves relevant tools via semantic search, runs the LLM tool-call loop (up to `max_iterations` or `max_execution_time_s`), offloads tool outputs to the Tool Log, refreshes context after memory-mutating tools, and persists workflows, entities, and the assistant response after each run. `call_agent_naive()` is a deliberately stripped-down version that removes tool offloading, summarization tools, context refresh, and memory reads — used for the head-to-head comparison in Task 4.

</details>


The first cells restore credentials, reconnect to the database, and initialize the full agent stack in one pass.

1. Run the credential restoration cell. You'll be prompted for your OpenAI and (optional) Tavily API keys.

2. Run the initialization cell. It creates the connection, MemoryManager, Toolbox, registers all tools, and calls `init_agent()`.

3. You should see "Full agent stack initialized — Proteus is ready".

    > **What's happening:** The `init_agent()` function sets module-level references in `proteus.agent` so that `call_agent()` can access the MemoryManager, Toolbox, and OpenAI client without passing them as arguments every time.

## Task 2: Run Proteus Through Research Scenarios

Each scenario uses `call_agent()` — the turn-level harness that builds context from memory, retrieves tools, runs the LLM tool-call loop, and persists results.

### Scenario 1: Simple Literature Query

1. Run the first scenario cell. Proteus searches the knowledge base for papers on transformer architectures for time-series forecasting.

    > **Watch for:** The context window display shows all five memory sections loaded. Proteus should find relevant papers from the arXiv dataset you ingested in Lab 2.

### Scenario 2: Follow-up on the Same Session

1. Run the second scenario cell. Same `thread_id` — Proteus should recall the previous turn from conversational memory.

    > **Watch for:** Proteus references the prior conversation and may call `search_tavily()` to find more recent work. If it does, the results are automatically persisted to the knowledge base.

### Scenario 3: New Research Thread

1. Run the third scenario. A fresh `thread_id` with a completely different topic (flow matching for generative models).

    > **Watch for:** Proteus starts with a clean conversational memory for this thread, but the knowledge base and entity memory may contain relevant information from earlier scenarios.

### Scenario 4: Cross-Referencing Prior Research

1. Run the fourth scenario. Proteus should recall entities and papers from Scenarios 1-2 and connect them to the flow matching topic.

    > **Watch for:** Entity memory provides continuity — paper titles and author names extracted in earlier scenarios are available here even though this is a different thread.

### Visualize Context Window Growth

1. Run the matplotlib cell. The chart shows estimated token usage per iteration across all scenarios.

    > **Key observation:** Context size should stay relatively flat or decrease after summarization, rather than growing unboundedly.

## Task 3: Baseline — The Naive Agent

The naive agent (`call_agent_naive`) deliberately removes the key optimizations:

| Technique Removed | Effect |
|---|---|
| **Tool output offloading** | Full raw outputs stay in messages — each tool call adds thousands of tokens |
| **Summarization tools** | Agent can't compact context — it only grows, never shrinks |
| **Context refresh after search** | Stale + bloated context persists across iterations |
| **Memory-backed context rebuild** | No separation of concerns — everything accumulates |

## Task 4: Head-to-Head Comparison

1. Run the comparison cell. Three progressive queries are sent to both agents with a 15-second pause between calls to stay within API rate limits:

    * "Search for recent papers on AI agent memory published in 2025 or 2026."
    * "Pick the most interesting paper and give me the key takeaways."
    * "Summarize everything we've discussed so far."

    > **Note on rate limits:** The comparison uses `max_iterations=3` and a 15-second delay between calls to stay within OpenAI's token-per-minute limits. If you have a higher-tier API plan, you can reduce `DELAY_SECONDS` in the notebook cell.

2. Run the visualization cell. The chart overlays both agents' context growth on the same axes.

    > **Expected result:** The engineered agent's context stays manageable while the naive agent's grows linearly (or worse) with each tool call.

## Task 5: Launch the Streamlit Chat UI

<details><summary>🔍 View source: <code>proteus/app.py</code> — Streamlit chat interface for Proteus</summary>

```python
"""
Proteus Chat UI
===============
Streamlit-based chat interface for the SeerGroup Research Assistant.

Run with:
    streamlit run proteus/app.py --server.port 8501
"""

import os
import uuid

import streamlit as st

# ── Page config ───────────────────────────────────────────
st.set_page_config(page_title="Proteus — SeerGroup Research Assistant", page_icon="🔬", layout="wide")
st.title("🔬 Proteus — SeerGroup Research Assistant")
st.caption("Memory-powered AI agent backed by Oracle AI Database 26ai")

# ── Sidebar: credentials & status ─────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    db_dsn = st.text_input("Database DSN", value=os.environ.get("PROTEUS_DB_DSN", ""))
    db_password = st.text_input("VECTOR password", type="password",
                                value=os.environ.get("PROTEUS_DB_PASSWORD", ""))
    openai_key = st.text_input("OpenAI API key", type="password",
                               value=os.environ.get("OPENAI_API_KEY", ""))
    tavily_key = st.text_input("Tavily API key (optional)", type="password",
                               value=os.environ.get("TAVILY_API_KEY", ""))
    model = st.selectbox("Model", ["gpt-4o", "gpt-4-turbo", "gpt-5", "gpt-5-mini"], index=0)

    init_button = st.button("🚀 Initialize Proteus", type="primary", use_container_width=True)

# ── Session state ─────────────────────────────────────────
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())[:8]

# ── Initialization ────────────────────────────────────────
if init_button:
    if not db_dsn or not db_password or not openai_key:
        st.sidebar.error("Please fill in DSN, VECTOR password, and OpenAI key.")
    else:
        with st.spinner("Initializing Proteus..."):
            # Set environment variables for proteus modules
            os.environ["PROTEUS_DB_DSN"] = db_dsn
            os.environ["PROTEUS_DB_PASSWORD"] = db_password
            os.environ["OPENAI_API_KEY"] = openai_key
            os.environ["PROTEUS_MODEL"] = model
            if tavily_key:
                os.environ["TAVILY_API_KEY"] = tavily_key

            try:
                from proteus import config as cfg
                # Force reload config with new env vars
                cfg.DB_DSN = db_dsn
                cfg.DB_PASSWORD = db_password
                cfg.OPENAI_MODEL = model

                from proteus.db import connect_to_oracle, drop_all_tables
                from proteus.db import create_conversational_history_table, create_tool_log_table
                from proteus.vector_store import get_embedding_model, create_all_vector_stores
                from proteus.memory_manager import MemoryManager
                from proteus.toolbox import Toolbox
                from proteus.tools import init_tools
                from proteus.agent import init_agent

                from openai import OpenAI

                conn = connect_to_oracle(user="VECTOR", password=db_password, dsn=db_dsn)
                drop_all_tables(conn)

                conv_table = create_conversational_history_table(conn)
                tool_log_table = create_tool_log_table(conn)

                emb_model = get_embedding_model()
                stores = create_all_vector_stores(conn, emb_model)

                mm = MemoryManager(
                    conn=conn,
                    conversation_table=conv_table,
                    knowledge_base_vs=stores["knowledge_base_vs"],
                    workflow_vs=stores["workflow_vs"],
                    toolbox_vs=stores["toolbox_vs"],
                    entity_vs=stores["entity_vs"],
                    summary_vs=stores["summary_vs"],
                    tool_log_table=tool_log_table,
                )

                client = OpenAI()
                tb = Toolbox(memory_manager=mm, llm_client=client, embedding_model=emb_model)
                init_tools(mm, tb, client, tavily_api_key=tavily_key)
                init_agent(mm, tb, client)

                st.session_state.initialized = True
                st.session_state.agent_call = __import__("proteus.agent", fromlist=["call_agent"]).call_agent
                st.sidebar.success("✅ Proteus initialized!")

            except Exception as e:
                st.sidebar.error(f"Initialization failed: {e}")
                st.session_state.initialized = False

# ── Chat display ──────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────
if not st.session_state.initialized:
    st.info("👈 Configure credentials in the sidebar and click **Initialize Proteus** to start chatting.")
else:
    if prompt := st.chat_input("Ask Proteus a research question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Proteus is thinking..."):
                try:
                    answer = st.session_state.agent_call(
                        prompt, thread_id=st.session_state.thread_id
                    )
                except Exception as e:
                    answer = f"Error: {e}"
                st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})

    # Sidebar: session info
    with st.sidebar:
        st.divider()
        st.caption(f"Session: `{st.session_state.thread_id}`")
        if st.button("🔄 New session"):
            st.session_state.thread_id = str(uuid.uuid4())[:8]
            st.session_state.messages = []
            st.rerun()

```

**What this code does:** The Streamlit app provides a browser-based chat interface for Proteus. The sidebar collects database DSN, VECTOR password, OpenAI key, and optional Tavily key. On clicking 'Initialize Proteus', it runs the full initialization sequence: connect to Oracle, create tables, build vector stores, initialize MemoryManager, Toolbox, tools, and agent. Chat messages are stored in `st.session_state` for display continuity. Each user message is routed through `call_agent()` with a persistent thread ID. A 'New session' button generates a fresh thread ID and clears the chat history.

</details>


1. Run the final cell to start the Streamlit app:

    ```python
    !streamlit run proteus/app.py --server.port 8501 --server.headless true
    ```

2. Open your browser to **http://localhost:8501**.

3. In the sidebar, enter your database DSN, VECTOR password, and OpenAI API key. Click **Initialize Proteus**.

4. Chat with Proteus! Try questions like:
    * "What papers do you have about attention mechanisms?"
    * "Search the web for the latest work on retrieval-augmented generation."
    * "Summarize our conversation so far."

    > **Note:** The Streamlit app will block the notebook cell while running. Press `Ctrl+C` or interrupt the kernel to stop it.

## Key Takeaways

### Agent Architecture Concepts

In OpenAI-style framing, an **agent run** is what `call_agent(...)` executes — one user turn handled. Within a run, the **tool-call loop** repeats: model reasoning, optional tool calls, harness executes tools, model observes results, repeat until a final answer.

An **agent harness** is the runtime scaffolding around that loop. In this workshop, it is a **memory-based agent harness** where context is assembled from multiple memory types each run, tools are discovered and executed within the run, outputs are written back into memory for future runs, and summaries compact context while preserving continuity.

### What Makes the Difference

| Aspect | Naive Agent | Proteus (Engineered) |
|--------|-------------|---------------------|
| **Context growth** | Unbounded — every tool output accumulates | Managed — tool outputs offloaded, conversations compacted |
| **Memory** | None — only raw message history | 7 specialized types with semantic search |
| **Tool discovery** | All tools all the time | Semantic retrieval of relevant tools per query |
| **Knowledge retention** | Lost between sessions | Persistent across research sessions |
| **Resolution patterns** | Rediscovered every time | Learned workflows reused automatically |

### The Practical Takeaway

Strong agents are not just model prompts. They are **run + harness systems**, and memory engineering is the control layer that makes them reliable, stateful, and scalable. The key discipline is deciding what should be stored, retrieved, summarized, and refreshed — and how to keep context windows relevant, not just large.

## 🎉 Workshop Complete!

You've built a complete memory-powered AI research assistant:

| Lab | What You Built |
|-----|---------------|
| **1** | Deployed Oracle Autonomous DB and created VECTOR user |
| **2** | Vector search + memory architecture + MemoryManager + Toolbox |
| **3** | Context engineering + summarization + web search |
| **4** | Agent harness + scenarios + comparison + Streamlit UI |

Proteus demonstrates how modern AI agents maintain context, learn from interactions, and manage information across sessions — all backed by Oracle AI Database 26ai as the converged storage layer for relational, vector, and semantic data.

## Learn More

* [OpenAI Function Calling Documentation](https://platform.openai.com/docs/guides/function-calling)
* [Streamlit Chat Elements](https://docs.streamlit.io/develop/api-reference/chat)
* [Oracle AI Vector Search](https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/)

## Acknowledgements

* **Author(s)** - Richmond Alake
* **Contributors** - Eli Schilling
* **Last Updated By/Date** - Published February, 2026
