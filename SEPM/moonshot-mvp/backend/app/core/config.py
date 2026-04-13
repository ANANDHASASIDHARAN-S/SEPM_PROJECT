from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SRM Cybersecurity Moonshot API"
    database_url: str = "postgresql+psycopg2://moonshot:moonshot@localhost:5432/moonshot"
    elasticsearch_url: str = "http://localhost:9200"
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:3000"
    siem_ingest_api_key: str = "local-dev-siem-key"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
