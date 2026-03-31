from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    database_url: str
    db_schema: str = 'scor'
    db_rebuild_on_start: bool = False

    auth_mode: str = 'entra'
    entra_tenant_id: str
    entra_audience: str
    reception_group_id: str | None = None

    app_public_url: str = 'http://localhost:5173'

    graph_client_id: str | None = None
    graph_client_secret: str | None = None
    sharepoint_site_id: str | None = None
    sharepoint_drive_id: str | None = None
    sharepoint_root_folder: str = 'scor-wnioski'

    mssql_car_groups_url: str | None = None


settings = Settings()
