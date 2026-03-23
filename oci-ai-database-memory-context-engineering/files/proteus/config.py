"""
Proteus Configuration
=====================
Centralized settings for the SeerGroup Research Assistant.
Reads from environment variables, falling back to defaults.

Credential flow:
  - Lab 1 notebook sets %store vars and writes os.environ
  - Subsequent notebooks do %store -r then set os.environ before importing proteus
  - All proteus modules read from os.environ via this config
"""

import os

# ── Database ──────────────────────────────────────────────
DB_USER = os.environ.get("PROTEUS_DB_USER", "VECTOR")
DB_PASSWORD = os.environ.get("PROTEUS_DB_PASSWORD", "")
DB_DSN = os.environ.get("PROTEUS_DB_DSN", "")
DB_ADMIN_USER = os.environ.get("PROTEUS_DB_ADMIN_USER", "ADMIN")
DB_ADMIN_PASSWORD = os.environ.get("PROTEUS_DB_ADMIN_PASSWORD", "")

# ── LLM ───────────────────────────────────────────────────
OPENAI_MODEL = os.environ.get("PROTEUS_MODEL", "gpt-4o")

# ── Embedding ─────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-mpnet-base-v2"

# ── Table names ───────────────────────────────────────────
CONVERSATIONAL_TABLE = "CONVERSATIONAL_MEMORY"
KNOWLEDGE_BASE_TABLE = "SEMANTIC_MEMORY"
WORKFLOW_TABLE = "WORKFLOW_MEMORY"
TOOLBOX_TABLE = "TOOLBOX_MEMORY"
ENTITY_TABLE = "ENTITY_MEMORY"
SUMMARY_TABLE = "SUMMARY_MEMORY"
TOOL_LOG_TABLE = "TOOL_LOG"

ALL_TABLES = [
    CONVERSATIONAL_TABLE, KNOWLEDGE_BASE_TABLE, WORKFLOW_TABLE,
    TOOLBOX_TABLE, ENTITY_TABLE, SUMMARY_TABLE, TOOL_LOG_TABLE,
]

# ── Model token limits (for context management) ──────────
MODEL_TOKEN_LIMITS = {
    "gpt-5": 256000,
    "gpt-5-mini": 128000,
    "gpt-4o": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
}

# ── Streamlit app ─────────────────────────────────────────
APP_PORT = int(os.environ.get("PROTEUS_APP_PORT", "8501"))
APP_TITLE = "Proteus — SeerGroup Research Assistant"
