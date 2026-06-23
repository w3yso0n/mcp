import logging
from typing import Any

import pyodbc

from config import settings

logger = logging.getLogger(__name__)

PREFERRED_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "SQL Server",
]

_resolved_driver: str | None = None


def get_available_drivers() -> list[str]:
    return list(pyodbc.drivers())


def resolve_driver() -> str:
    global _resolved_driver
    if _resolved_driver:
        return _resolved_driver

    available = get_available_drivers()
    configured = settings.mssql_driver.strip()

    if configured and configured.lower() != "auto":
        if configured in available:
            _resolved_driver = configured
            logger.info("ODBC: usando driver configurado '%s'", configured)
            return _resolved_driver

        logger.warning(
            "ODBC: driver configurado '%s' NO instalado. Disponibles: %s",
            configured,
            available or ["(ninguno)"],
        )

    for driver in PREFERRED_DRIVERS:
        if driver in available:
            _resolved_driver = driver
            if configured and configured.lower() != "auto":
                logger.warning(
                    "ODBC: auto-seleccionado '%s' (en lugar de '%s')",
                    driver,
                    configured,
                )
            else:
                logger.info("ODBC: auto-seleccionado '%s'", driver)
            return _resolved_driver

    raise RuntimeError(
        f"No hay driver ODBC para SQL Server. "
        f"MSSQL_DRIVER='{configured}'. "
        f"Instalados: {available or ['(ninguno)']}. "
        f"En Docker/Linux instala msodbcsql18 y usa 'ODBC Driver 18 for SQL Server'."
    )


def get_odbc_diagnostics() -> dict[str, Any]:
    configured = settings.mssql_driver.strip()
    available = get_available_drivers()
    diagnostics: dict[str, Any] = {
        "configured_driver": configured,
        "available_drivers": available,
        "resolved_driver": None,
        "driver_ok": False,
        "platform_hint": (
            "Docker/Linux requiere 'ODBC Driver 18 for SQL Server'. "
            "'SQL Server' solo existe en Windows."
        ),
    }

    try:
        resolved = resolve_driver()
        diagnostics["resolved_driver"] = resolved
        diagnostics["driver_ok"] = True
    except RuntimeError as exc:
        diagnostics["error"] = str(exc)

    return diagnostics
