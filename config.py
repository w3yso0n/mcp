from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mssql_server: str = "localhost"
    mssql_database: str = "master"
    mssql_user: str = "sa"
    mssql_password: str = ""
    mssql_driver: str = "ODBC Driver 18 for SQL Server"
    mssql_trust_server_certificate: bool = True
    mssql_readonly: bool = True
    mssql_query_row_limit: int = 100


settings = Settings()
