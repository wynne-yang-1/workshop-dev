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
