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
