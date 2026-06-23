from typing import Any

from pydantic import BaseModel, Field

from db import describe_table, list_tables, run_query


class QueryRequest(BaseModel):
    sql: str = Field(..., examples=["SELECT TOP 5 * FROM dbo.TuTabla"])


def api_list_tables(schema: str = "dbo") -> dict[str, Any]:
    tables = list_tables(schema)
    return {"schema": schema, "count": len(tables), "tables": tables}


def api_describe_table(schema: str, table: str) -> dict[str, Any]:
    return describe_table(schema, table)


def api_run_query(body: QueryRequest) -> dict[str, Any]:
    return run_query(body.sql)
