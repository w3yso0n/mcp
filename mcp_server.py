import json

from mcp.server.fastmcp import FastMCP

from db import describe_table, list_tables, run_query

mcp = FastMCP("sql-server-mcp", stateless_http=True, json_response=True)


@mcp.tool()
def list_tables_tool(schema: str = "dbo") -> str:
    """Lista las tablas disponibles en un esquema de SQL Server."""
    try:
        tables = list_tables(schema)
        return json.dumps({"schema": schema, "tables": tables}, ensure_ascii=False, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


@mcp.tool()
def describe_table_tool(schema: str, table: str) -> str:
    """Describe columnas, tipos y claves primarias de una tabla."""
    try:
        metadata = describe_table(schema, table)
        return json.dumps(metadata, ensure_ascii=False, indent=2, default=str)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


@mcp.tool()
def run_query_tool(sql: str) -> str:
    """Ejecuta una consulta de solo lectura (SELECT o WITH). Máximo 100 filas."""
    try:
        result = run_query(sql)
        return json.dumps(result, ensure_ascii=False, indent=2, default=str)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
