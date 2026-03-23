"""
Proteus Database Layer
======================
Connection helpers and DDL for memory tables.
"""

import time
import oracledb
from proteus import config


def connect_to_oracle(
    max_retries: int = 3,
    retry_delay: int = 5,
    user: str = None,
    password: str = None,
    dsn: str = None,
    program: str = "seergroup.proteus.workshop",
) -> oracledb.Connection:
    """Connect to Oracle database with retry logic and helpful error messages."""
    user = user or config.DB_USER
    password = password or config.DB_PASSWORD
    dsn = dsn or config.DB_DSN

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Connection attempt {attempt}/{max_retries}...")
            conn = oracledb.connect(user=user, password=password, dsn=dsn, program=program)
            print("✓ Connected successfully!")

            with conn.cursor() as cur:
                cur.execute("SELECT banner FROM v$version WHERE banner LIKE 'Oracle%'")
                banner = cur.fetchone()[0]
                print(f"\n{banner}")

            return conn

        except oracledb.OperationalError as e:
            error_msg = str(e)
            print(f"✗ Connection failed (attempt {attempt}/{max_retries})")

            if "DPY-4011" in error_msg or "Connection reset by peer" in error_msg:
                print("  → Database may still be starting. Retrying...")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise
            else:
                raise

    raise ConnectionError("Failed to connect after all retries")


# ── DDL helpers ───────────────────────────────────────────

def drop_all_tables(conn: oracledb.Connection) -> None:
    """Drop all memory tables (idempotent)."""
    for table in config.ALL_TABLES:
        try:
            with conn.cursor() as cur:
                cur.execute(f"DROP TABLE {table} PURGE")
            print(f"  ✓ Dropped {table}")
        except Exception as e:
            if "ORA-00942" in str(e):
                print(f"  - {table} (not exists)")
            else:
                print(f"  ✗ {table}: {e}")
    conn.commit()


def create_conversational_history_table(
    conn: oracledb.Connection,
    table_name: str = None,
) -> str:
    """Create the conversational memory SQL table with indexes."""
    table_name = table_name or config.CONVERSATIONAL_TABLE
    with conn.cursor() as cur:
        try:
            cur.execute(f"DROP TABLE {table_name}")
        except Exception:
            pass

        cur.execute(f"""
            CREATE TABLE {table_name} (
                id VARCHAR2(100) DEFAULT SYS_GUID() PRIMARY KEY,
                thread_id VARCHAR2(100) NOT NULL,
                role VARCHAR2(50) NOT NULL,
                content CLOB NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata CLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                summary_id VARCHAR2(100) DEFAULT NULL
            )
        """)
        cur.execute(f"CREATE INDEX idx_{table_name.lower()}_thread_id ON {table_name}(thread_id)")
        cur.execute(f"CREATE INDEX idx_{table_name.lower()}_timestamp ON {table_name}(timestamp)")

    conn.commit()
    print(f"✅ Table {table_name} created with indexes (thread_id, timestamp)")
    return table_name


def create_tool_log_table(
    conn: oracledb.Connection,
    table_name: str = None,
) -> str:
    """Create the tool log SQL table (experimental / episodic memory)."""
    table_name = table_name or config.TOOL_LOG_TABLE
    with conn.cursor() as cur:
        try:
            cur.execute(f"DROP TABLE {table_name}")
        except Exception:
            pass

        cur.execute(f"""
            CREATE TABLE {table_name} (
                id VARCHAR2(100) DEFAULT SYS_GUID() PRIMARY KEY,
                thread_id VARCHAR2(100) NOT NULL,
                tool_call_id VARCHAR2(200) NOT NULL,
                tool_name VARCHAR2(200) NOT NULL,
                tool_args CLOB,
                tool_output CLOB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute(f"CREATE INDEX idx_{table_name.lower()}_thread ON {table_name}(thread_id)")

    conn.commit()
    print(f"✅ Table {table_name} created")
    return table_name
