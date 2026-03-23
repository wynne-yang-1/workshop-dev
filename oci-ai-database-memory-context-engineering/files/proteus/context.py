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
