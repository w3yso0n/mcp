from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from api import QueryRequest, api_describe_table, api_list_tables, api_run_query
from dashboard import render_dashboard
from db import check_connection, list_tables
from mcp_server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="MCP Base API",
    description="API base con servidor MCP Streamable HTTP para SQL Server",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/mcp-server", mcp.streamable_http_app())


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    connection = check_connection()
    tables: list[dict[str, str]] = []
    tables_error: str | None = None

    if connection["connected"]:
        try:
            tables = list_tables("dbo")
        except Exception as exc:
            tables_error = str(exc)

    base_url = str(request.base_url).rstrip("/")
    return render_dashboard(connection, tables, tables_error, base_url)


@app.get("/health")
def health():
    connection = check_connection()
    return {
        "status": "healthy" if connection["connected"] else "degraded",
        "service": "mcp-base-api",
        "mcp_endpoint": "/mcp-server/mcp",
        "database_connected": connection["connected"],
        "database": connection["database"],
        "server": connection["server"],
    }


@app.get("/api/tables", tags=["Tools GUI"])
def get_tables(schema: str = Query(default="dbo", description="Esquema SQL")):
    """Equivalente a list_tables_tool — usable desde Swagger o el dashboard."""
    try:
        return api_list_tables(schema)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/tables/{schema}/{table}", tags=["Tools GUI"])
def get_table_description(schema: str, table: str):
    """Equivalente a describe_table_tool."""
    try:
        return api_describe_table(schema, table)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/query", tags=["Tools GUI"])
def post_query(body: QueryRequest):
    """Equivalente a run_query_tool — solo SELECT / WITH."""
    try:
        return api_run_query(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
