# MCP SQL Server

Servidor MCP con transporte **Streamable HTTP** montado en FastAPI, con tools de solo lectura sobre SQL Server.

## Requisitos

- Python 3.12+
- [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) (en Windows, normalmente ya instalado o descargable desde Microsoft)

## Configuración

1. Copia `.env.example` a `.env` y completa las credenciales:

```bash
cp .env.example .env
```

2. Instala dependencias:

```bash
pip install -r requirements.txt
```

3. Inicia el servidor:

```bash
uvicorn main:app --reload --port 8000
```

4. Verifica el health check: [http://localhost:8000/health](http://localhost:8000/health)

## Conectar Cursor

El endpoint MCP es: `http://localhost:8000/mcp-server/mcp`

Puedes usar el archivo de ejemplo [`.cursor/mcp.json`](.cursor/mcp.json) o configurarlo en **Settings → MCP**:

```json
{
  "mcpServers": {
    "sql-server": {
      "url": "http://localhost:8000/mcp-server/mcp"
    }
  }
}
```

## Tools disponibles

| Tool | Descripción |
|------|-------------|
| `list_tables_tool` | Lista tablas de un esquema (default `dbo`) |
| `describe_table_tool` | Columnas, tipos y PK de una tabla |
| `run_query_tool` | Ejecuta `SELECT` / `WITH` (máx. 100 filas) |

## Docker

```bash
docker build -t mcp-sql-server .
docker run --env-file .env -p 8000:8000 mcp-sql-server
```

## Usuario SQL recomendado

Cuenta de solo lectura con `db_datareader` y permiso `VIEW DEFINITION` para consultar metadatos del esquema.
