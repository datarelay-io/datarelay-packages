"""
DataRelay SQL Server integration.

Reads connection details and query from decrypted DR_* env vars,
executes the query, and writes the result to a JSON file.

Connection can be provided as either:
  - DR_DB_CONNECTION_STRING  e.g. "mssql+pyodbc://user:pass@host/db?driver=ODBC+Driver+18+for+SQL+Server"
  - Individual params: DR_DB_HOST, DR_DB_USER, DR_DB_PASSWORD, DR_DB_DATABASE
    (DR_DB_PORT defaults to 1433, DR_DB_DRIVER defaults to "ODBC Driver 18 for SQL Server")

The query comes from DR_QUERY. The output path defaults to DR_KEY.
Call decrypt_params() first (or use run_query() which calls it internally).
"""

import json
import os
from datetime import datetime, timezone
from .crypto import decrypt_params


def _build_connection_string(prefix: str) -> str:
    """Build a SQLAlchemy connection string from DR_* env vars."""
    conn_str = os.environ.get(f"{prefix}DB_CONNECTION_STRING")
    if conn_str:
        return conn_str

    host = os.environ.get(f"{prefix}DB_HOST", "")
    user = os.environ.get(f"{prefix}DB_USER", "")
    password = os.environ.get(f"{prefix}DB_PASSWORD", "")
    database = os.environ.get(f"{prefix}DB_DATABASE", "")
    port = os.environ.get(f"{prefix}DB_PORT", "1433")
    driver = os.environ.get(f"{prefix}DB_DRIVER", "ODBC Driver 18 for SQL Server")

    missing = [k for k, v in {
        f"{prefix}DB_HOST": host,
        f"{prefix}DB_USER": user,
        f"{prefix}DB_PASSWORD": password,
        f"{prefix}DB_DATABASE": database,
    }.items() if not v]
    if missing:
        raise ValueError(
            f"Missing connection params: {', '.join(missing)}. "
            f"Provide {prefix}DB_CONNECTION_STRING or all of "
            f"{prefix}DB_HOST, {prefix}DB_USER, {prefix}DB_PASSWORD, {prefix}DB_DATABASE."
        )

    driver_safe = driver.replace(" ", "+")
    return f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver={driver_safe}&TrustServerCertificate=yes"


def run_query(
    output_path: str | None = None,
    master: str | None = None,
    prefix: str | None = None,
) -> str:
    """
    Decrypt DR_* params, run DR_QUERY against SQL Server, write result to JSON.

    Args:
        output_path: Path to write the JSON file. Defaults to DR_KEY.
        master: MASTER_CURRENT key. Defaults to MASTER_CURRENT env var.
        prefix: Param prefix. Defaults to PARAM_PREFIX env var or "DR_".

    Returns:
        The path the file was written to.

    Example:
        from datarelay.sql_server import run_query
        run_query()
    """
    try:
        import sqlalchemy as sa
    except ImportError:
        raise ImportError("sqlalchemy is required: pip install sqlalchemy pyodbc")

    prefix = prefix or os.environ.get("PARAM_PREFIX", "DR_")

    # Decrypt all encrypted DR_* vars — writes plaintext back into os.environ
    decrypt_params(master=master, prefix=prefix)

    query = os.environ.get(f"{prefix}QUERY", "")
    if not query:
        raise ValueError(f"No query found — set {prefix}QUERY in DataRelay")

    conn_str = _build_connection_string(prefix)
    engine = sa.create_engine(conn_str, pool_pre_ping=True)

    with engine.connect() as conn:
        result = conn.execute(sa.text(query))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]

    output = {
        "rows": rows,
        "count": len(rows),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    path = output_path or os.environ.get(f"{prefix}KEY") or "result.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, default=str, indent=2)

    return path
