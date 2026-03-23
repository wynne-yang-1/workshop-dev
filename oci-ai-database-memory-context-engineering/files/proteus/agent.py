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
