from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
  SANDBOX_API_KEY: str
  SANDBOX_SECRET: str
  PROD_API_KEY: str
  PROD_SECRET: str
  ACCOUNT_ID_KEY: str
  DATABASE_PATH: str = "data/trade_bot.sqlite3"

  OPENAI_API_KEY: str
  OPENAI_MODEL: str = "gpt-5-mini"

  # Tell Pydantic to read from a .env file
  model_config = SettingsConfigDict(env_file=ENV_FILE)


# Instantiate settings to be imported elsewhere
settings = Settings()
