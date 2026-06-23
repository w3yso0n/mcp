import logging
from typing import Any

import pyodbc

from config import settings

logger = logging.getLogger(__name__)


def get_available_drivers() -> list[str]:
    return list(pyodbc.drivers())


def get_odbc_diagnostics() -> dict[str, Any]:
    return {
        "configured_driver": settings.mssql_driver_configured or settings.mssql_driver,
        "resolved_driver": settings.mssql_driver,
        "available_drivers": get_available_drivers(),
        "driver_ok": bool(settings.mssql_driver),
        "platform_hint": (
            "Docker/Linux requiere 'ODBC Driver 18 for SQL Server'. "
            "'SQL Server' solo existe en Windows."
        ),
    }
