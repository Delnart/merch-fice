from pydantic import Field, Json
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str = Field(validation_alias="BOT_TOKEN")
    webhook_secret: str = Field(validation_alias="WEBHOOK_SECRET")
    database_url: str = Field(validation_alias="DATABASE_URL")
    app_base_url: str = Field(validation_alias="APP_BASE_URL")
    admin_default_currency: str = Field(default="UAH", validation_alias="ADMIN_DEFAULT_CURRENCY")
    
    google_creds_json: Json = Field(validation_alias="GOOGLE_CREDS_JSON")
    google_sheets_id: str = Field(validation_alias="GOOGLE_SHEETS_ID")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()