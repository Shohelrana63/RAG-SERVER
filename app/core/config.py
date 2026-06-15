from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongodb_uri: str = "mongodb://localhost:27017/ai_pdf_assistant"
    jwt_access_secret: str = "change_me_access_secret"
    jwt_algorithm: str = "HS256"
    jwt_access_expires_minutes: int = 15
    client_url: str = "http://localhost:3000"


settings = Settings()
