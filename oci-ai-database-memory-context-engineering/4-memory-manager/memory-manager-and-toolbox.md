# Lab 4: Building the Memory Manager & Toolbox

## The MemoryManager Class and Semantic Tool Discovery

--------

### Objective

In this lab, you'll implement the two core abstractions that power Proteus:

1. **MemoryManager** — a unified class with read/write methods for all six memory types
2. **Toolbox** — a semantic tool registry where tools are discovered by meaning, not by name

By the end, you'll be able to test individual memory operations: write a conversation message, search the knowledge base, register a tool, and retrieve it via natural language query.

--------

## Task 1: The MemoryManager Class

The `MemoryManager` is the central abstraction that unifies all memory operations. It provides a clean interface for reading and writing to different memory types, hiding the complexity of SQL queries and vector store operations.

### Key Features

- **Thread-based conversations** — Messages are organized by `thread_id` (one per support ticket)
- **Semantic search** — Vector stores enable finding relevant content by meaning
- **Metadata filtering** — Workflows filter by `num_steps > 0`, summaries filter by `id`
- **LLM-powered entity extraction** — Automatically extracts servers, services, and people from text
- **Formatted context output** — Each read method returns formatted text ready for the LLM context window

### Alternative Frameworks

There are existing frameworks that abstract memory management for AI agents:

| Framework | Description |
|-----------|-------------|
| **LangChain Memory** | Built-in memory classes (ConversationBufferMemory, VectorStoreRetrieverMemory) |
| **Mem0** | Dedicated memory layer for AI agents with automatic memory management |
| **LlamaIndex** | Document-based memory with various storage backends |
| **Zep** | Long-term memory service for AI assistants |

For learning purposes, building your own memory manager (as we do here) gives you a deep understanding of how memory engineering works. For production, you might consider using or extending an existing framework. Note that this workshop only illustrates reads and writes — a production system would also need deletion, updates, and TTL-based expiry.

--------

### The Implementation

```python
import json as json_lib
from datetime import datetime


class MemoryManager:
    """
    Memory manager for AI agents using Oracle AI Database.

    Manages 7 types of memory:
    - Conversational: Chat history per ticket thread (SQL table)
    - Knowledge Base: Searchable documents and KB articles (vector-enabled SQL table)
    - Workflow: Learned resolution patterns (vector-enabled SQL table)
    - Toolbox: Available diagnostic tools (vector-enabled SQL table)
    - Entity: Servers, services, people, teams (vector-enabled SQL table)
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
        return f"""## Conversation Memory (Ticket: {thread_id})
### Purpose: Recent dialogue turns that have NOT yet been summarized.
### When to use: Refer to this for the user's latest questions, your prior answers,
### and any commitments or follow-ups from the current troubleshooting session.
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
### Purpose: KB articles, runbooks, vendor docs, and web search results stored for long-term reference.
### When to use: Cite specific facts, resolution steps, or incident details from here before
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
### Purpose: Step-by-step records of how similar past tickets were resolved.
### When to use: Before planning a multi-step resolution, check if a similar workflow
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
        """Use LLM to extract entities (servers, services, people, teams) from text."""
        if not text or len(text.strip()) < 5:
            return []

        prompt = f'''Extract entities from: "{text[:500]}"
Return JSON: [{{"name": "X", "type": "SERVER|SERVICE|PERSON|TEAM|SYSTEM", "description": "brief"}}]
If none: []'''

        try:
            response = llm_client.chat.completions.create(
                model="gpt-4o",
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
        except:
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
### Purpose: Named entities (servers, services, people, teams) extracted from conversations.
### When to use: Resolve references like "that server" or "the team we discussed".
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
            "### Purpose: Compressed snapshots of older troubleshooting sessions.",
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

--------

## Task 2: Initialize the Memory Manager

```python
memory_manager = MemoryManager(
    conn=vector_conn,
    conversation_table=CONVERSATION_HISTORY_TABLE,
    knowledge_base_vs=knowledge_base_vs,
    workflow_vs=workflow_vs,
    toolbox_vs=toolbox_vs,
    entity_vs=entity_vs,
    summary_vs=summary_vs,
    tool_log_table=TOOL_LOG_TABLE_NAME,
)
```

### Quick Smoke Test

Let's verify the memory manager works by writing and reading a test conversation:

```python
# Write a test conversation
test_thread = "TICKET-TEST-001"
memory_manager.write_conversational_memory("I can't log in to Jira this morning", "user", test_thread)
memory_manager.write_conversational_memory("Let me check AUTH-SVC status for you.", "assistant", test_thread)

# Read it back
print(memory_manager.read_conversational_memory(test_thread))
```

```python
# Test knowledge base search
print(memory_manager.read_knowledge_base("VPN keeps disconnecting"))
```

--------

## Task 3: The Semantic Toolbox

### The Scalability Problem with Tools

As your AI system grows, you might have **hundreds of tools** available — diagnostic scripts, API calls, database queries, search endpoints. Passing all tools to the LLM at inference time creates serious problems:

| Problem | Impact |
|---------|--------|
| **Context bloat** | Tool definitions consume tokens, leaving less room for actual content |
| **Tool selection failure** | LLMs struggle to choose the right tool when presented with too many options |
| **Increased latency** | More tokens = slower inference |
| **Higher costs** | More tokens = higher API costs |

Model providers typically recommend limiting tools to 10-20 max for reliable selection.

### The Solution: Semantic Tool Retrieval

The `Toolbox` class solves this by treating tools as a **searchable memory**:

1. **Register hundreds of tools** — Store all available tools with embeddings of their descriptions
2. **Retrieve only relevant tools** — At inference time, vector search finds tools semantically relevant to the current query
3. **Pass a focused toolset** — Only the top 3-5 retrieved tools are passed to the LLM

This means your system can **scale to hundreds of tools** while the LLM only sees the most relevant ones for each ticket.

### How It Works

```
User Query → Embed Query → Vector Search → Find tools with similar docstrings → Return relevant tools
```

The `augment=True` flag triggers LLM-powered enhancement:

1. **Docstring augmentation** — LLM rewrites the docstring to be clearer and more searchable
2. **Synthetic query generation** — LLM generates example queries that would need this tool
3. **Rich embedding** — Combines name + augmented docstring + signature + queries for better retrieval

This means a simple docstring like `"Search the web"` becomes a rich description that matches when the user asks `"What's the latest Kubernetes CVE?"`.

### Three Engineering Disciplines in One

| Discipline | Technique Used | How It Helps |
|------------|----------------|--------------|
| **Memory Engineering** | Toolbox as procedural memory | Tools are stored and retrieved like learned skills |
| **Memory Engineering** | Docstring augmentation | LLM improves descriptions for better retrieval |
| **Context Engineering** | Selective tool retrieval | Only relevant tools enter the context window |
| **Prompt Engineering** | Role setting | "You are a technical writer" improves docstring quality |

--------

### The Implementation

```python
import inspect
import uuid
from typing import Callable, Optional, Union
from pydantic import BaseModel


def get_embedding(text: str) -> list[float]:
    """Get the embedding for a text using the configured embedding model."""
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
    find relevant diagnostic tools based on natural language ticket descriptions.
    """

    def __init__(self, memory_manager, llm_client, model: str = "gpt-4o"):
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.model = model
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
            import json
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
                embedding = get_embedding(embedding_text)

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
                embedding = get_embedding(f"{f.__name__} {docstring} {signature}")
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

--------

## Task 4: Initialize the Toolbox and Set Up API Keys

```python
import os
import getpass


def set_env_securely(var_name, prompt):
    value = getpass.getpass(prompt)
    os.environ[var_name] = value
```

```python
set_env_securely("OPENAI_API_KEY", "OpenAI API Key: ")
```

```python
from openai import OpenAI

client = OpenAI()

# Initialize the Toolbox
toolbox = Toolbox(memory_manager=memory_manager, llm_client=client)
```

--------

## Task 5: Test Tool Registration and Retrieval

Let's register a simple diagnostic tool and verify semantic retrieval works:

```python
@toolbox.register_tool(augment=True)
def check_service_status(service_name: str) -> str:
    """Check if a SeerGroup internal service is running and return its status."""
    # In production, this would call a real monitoring API
    mock_statuses = {
        "auth-svc": "✅ Running (3 pods, 0 restarts)",
        "deploy-bot": "⚠️ Degraded (1/3 pods ready)",
        "ticket-bot": "✅ Running (2 pods, 0 restarts)",
    }
    return mock_statuses.get(
        service_name.lower(), f"❓ Unknown service: {service_name}"
    )
```

```python
# Test semantic retrieval — does the toolbox find this tool for a related query?
import pprint

retrieved_tools = memory_manager.read_toolbox("is the authentication service down?")
pprint.pprint(retrieved_tools)
```

> **🔍 Try it**: Change the query to something different — "check if deploy-bot is working" or "what services are having issues" — and see if the tool is still retrieved. This is semantic retrieval in action.

--------

## Lab 4 Recap

| What You Built | Why It Matters |
|---------------|----------------|
| `MemoryManager` class with 7 memory types | Unified read/write interface hiding SQL and vector complexity |
| Thread-based conversation read/write | Multi-ticket support with independent history per thread |
| Summary marking (not deletion) | Log compaction pattern — compress without losing audit trail |
| Entity extraction via LLM | Automatic recognition of servers, services, people from conversation |
| `Toolbox` class with semantic retrieval | Scale to hundreds of tools while LLM only sees relevant ones |
| LLM-augmented tool registration | Better retrieval through enhanced descriptions and synthetic queries |

**Key Insight**: The Toolbox sits at the intersection of three disciplines: *memory engineering* (tools as procedural memory), *context engineering* (only relevant tools in context), and *prompt engineering* (role-setting for better docstring augmentation).

**Next up**: In Lab 5, we'll build the context engineering layer — usage tracking, summarization, just-in-time retrieval — and integrate Tavily for web search.

## Learn More

- []()

## Acknowledgements

- **Author** - Richmond Alake
- **Contributors** - Eli Schilling
- **Last Updated By/Date** - Published February, 2026
