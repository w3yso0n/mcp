from fastapi import FastAPI

app = FastAPI(
    title="MCP Base API",
    description="API base para validar conexión MCP",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "MCP base establecida"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "mcp-base-api"
    }
