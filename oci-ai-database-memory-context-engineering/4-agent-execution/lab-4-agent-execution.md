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

## Task 1: Initialize the Agent

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

1. Run the comparison cell. Five progressive queries are sent to both agents:

    * "Search for recent papers on AI agent memory published in 2025 or 2026."
    * "Pick the most interesting paper and give me the key takeaways."
    * "What other approaches might that paper have missed?"
    * "Summarize everything we've discussed so far."
    * "What was the first question I asked?"

2. Run the visualization cell. The chart overlays both agents' context growth on the same axes.

    > **Expected result:** The engineered agent's context stays manageable while the naive agent's grows linearly (or worse) with each tool call.

## Task 5: Launch the Streamlit Chat UI

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
