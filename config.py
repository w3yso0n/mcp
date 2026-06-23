import sys

import pyodbc
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Self

PREFERRED_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "SQL Server",
]


def _pick_odbc_driver(configured: str) -> str:
    configured = configured.strip()
    available = pyodbc.drivers()

    if configured.lower() not in ("", "auto"):
        if configured in available:
            return configured
        print(
            f"[MCP-STARTUP] WARN: MSSQL_DRIVER='{configured}' no instalado. "
            f"Disponibles: {available}. Auto-seleccionando...",
            file=sys.stdout,
            flush=True,
        )

    for driver in PREFERRED_DRIVERS:
        if driver in available:
            return driver

    raise ValueError(
        f"No hay driver ODBC para SQL Server. MSSQL_DRIVER='{configured}'. "
        f"Instalados: {available or ['(ninguno)']}. "
        f"En Docker/Coolify instala msodbcsql18 y usa "
        f"'ODBC Driver 18 for SQL Server' o 'auto'."
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mssql_server: str = "localhost"
    mssql_database: str = "master"
    mssql_user: str = "sa"
    mssql_password: str = ""
    mssql_driver: str = "ODBC Driver 18 for SQL Server"
    mssql_driver_configured: str = ""
    mssql_trust_server_certificate: bool = True
    mssql_readonly: bool = True
    mssql_query_row_limit: int = 100
    app_version: str = "1.1.0"

    @model_validator(mode="after")
    def resolve_odbc_driver(self) -> Self:
        configured = self.mssql_driver.strip()
        object.__setattr__(self, "mssql_driver_configured", configured)
        object.__setattr__(self, "mssql_driver", _pick_odbc_driver(configured))
        return self


settings = Settings()

print(
    f"[MCP-STARTUP] Config cargada | app={settings.app_version} | "
    f"driver_config={settings.mssql_driver_configured!r} -> driver={settings.mssql_driver!r} | "
    f"odbc={pyodbc.drivers()}",
    flush=True,
)
