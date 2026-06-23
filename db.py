import logging
import re
import sys
from contextlib import contextmanager
from typing import Any

import pyodbc

from config import settings
from odbc_driver import get_available_drivers, get_odbc_diagnostics

logger = logging.getLogger(__name__)

FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|MERGE|GRANT|REVOKE|"
    r"DECLARE|OPENROWSET|OPENDATASOURCE|xp_|sp_executesql)\b",
    re.IGNORECASE,
)


def _startup_log(message: str, level: str = "info") -> None:
    print(f"[MCP-STARTUP] {message}", file=sys.stdout, flush=True)
    getattr(logger, level, logger.info)(message)


def build_connection_string() -> str:
    driver = settings.mssql_driver
    if driver.strip().lower() == "auto":
        raise RuntimeError(
            "El driver ODBC no fue resuelto (quedó 'auto'). "
            "Redeploy con la versión 1.1.0+ o usa MSSQL_DRIVER=ODBC Driver 18 for SQL Server."
        )
    trust_cert = "yes" if settings.mssql_trust_server_certificate else "no"
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={settings.mssql_server};"
        f"DATABASE={settings.mssql_database};"
        f"UID={settings.mssql_user};"
        f"PWD={settings.mssql_password};"
        f"TrustServerCertificate={trust_cert};"
    )


def log_startup_diagnostics() -> dict[str, Any]:
    diagnostics = get_odbc_diagnostics()
    _startup_log(f"=== Diagnóstico ODBC (app {settings.app_version}) ===")
    _startup_log(f"Servidor={settings.mssql_server} BD={settings.mssql_database} Usuario={settings.mssql_user}")
    _startup_log(f"MSSQL_DRIVER env={diagnostics['configured_driver']!r}")
    _startup_log(f"Driver resuelto={diagnostics['resolved_driver']!r}")
    _startup_log(f"Drivers instalados={diagnostics['available_drivers']}")

    connection = check_connection()
    if connection["connected"]:
        _startup_log(f"Conexión SQL Server OK — {connection.get('sql_version', '')}")
    else:
        _startup_log(f"Conexión SQL Server FALLO — {connection.get('error')}", "error")

    _startup_log("=== Fin diagnóstico ===")
    return {**diagnostics, "connection": connection}


@contextmanager
def get_connection():
    conn_str = build_connection_string()
    try:
        conn = pyodbc.connect(conn_str, timeout=30)
    except pyodbc.Error as exc:
        msg = (
            f"pyodbc error driver={settings.mssql_driver!r} server={settings.mssql_server} "
            f"db={settings.mssql_database}: {exc}"
        )
        _startup_log(msg, "error")
        raise
    try:
        yield conn
    finally:
        conn.close()


def _rows_to_dicts(cursor: pyodbc.Cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description or []]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def check_connection() -> dict[str, Any]:
    diagnostics = get_odbc_diagnostics()
    result: dict[str, Any] = {
        "connected": False,
        "server": settings.mssql_server,
        "database": settings.mssql_database,
        "driver_configured": diagnostics["configured_driver"],
        "driver_resolved": diagnostics["resolved_driver"],
        "available_drivers": get_available_drivers(),
        "readonly": settings.mssql_readonly,
        "sql_version": None,
        "error": None,
    }

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION AS version")
            row = cursor.fetchone()
            result["connected"] = True
            if row and row[0]:
                result["sql_version"] = str(row[0]).split("\n")[0]
    except Exception as exc:
        result["error"] = str(exc)
        logger.error("check_connection falló: %s", exc)
    return result


def list_tables(schema: str = "dbo") -> list[dict[str, str]]:
    query = """
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = ?
        ORDER BY TABLE_NAME
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, schema)
        return _rows_to_dicts(cursor)


def describe_table(schema: str, table: str) -> dict[str, Any]:
    columns_query = """
        SELECT
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.TABLE_SCHEMA = ? AND c.TABLE_NAME = ?
        ORDER BY c.ORDINAL_POSITION
    """
    pk_query = """
        SELECT kcu.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
            AND tc.TABLE_NAME = kcu.TABLE_NAME
        WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            AND tc.TABLE_SCHEMA = ?
            AND tc.TABLE_NAME = ?
        ORDER BY kcu.ORDINAL_POSITION
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(columns_query, schema, table)
        columns = _rows_to_dicts(cursor)
        if not columns:
            raise ValueError(f"La tabla '{schema}.{table}' no existe o no es accesible.")

        cursor.execute(pk_query, schema, table)
        primary_keys = [row["COLUMN_NAME"] for row in _rows_to_dicts(cursor)]

    return {
        "schema": schema,
        "table": table,
        "primary_keys": primary_keys,
        "columns": columns,
    }


def validate_readonly_query(sql: str) -> None:
    normalized = sql.strip().rstrip(";")
    if not normalized:
        raise ValueError("La consulta SQL está vacía.")

    if ";" in normalized:
        raise ValueError("Solo se permite una sentencia SQL por consulta.")

    if FORBIDDEN_SQL_PATTERN.search(normalized):
        raise ValueError("La consulta contiene operaciones no permitidas. Solo se aceptan SELECT o WITH.")

    first_token = normalized.split(maxsplit=1)[0].upper()
    if first_token not in {"SELECT", "WITH"}:
        raise ValueError("Solo se permiten consultas SELECT o WITH (CTE).")


def run_query(sql: str) -> dict[str, Any]:
    validate_readonly_query(sql)
    query = sql.strip().rstrip(";")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description or []]
        fetched = cursor.fetchmany(settings.mssql_query_row_limit)
        rows = [dict(zip(columns, row)) for row in fetched]

    return {
        "row_count": len(rows),
        "row_limit": settings.mssql_query_row_limit,
        "rows": rows,
    }
