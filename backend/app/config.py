from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'sqlite:///./mathmate.db'
    jwt_secret: str
    frontend_origin: str = 'http://localhost:3000'
    secure_cookies: bool = False
    ai_provider: Literal['mock', 'meta'] = 'mock'
    model_api_key: str = ''
    meta_model: str = 'muse-spark-1.3'


settings = Settings()
if len(settings.jwt_secret) < 32 or settings.jwt_secret.startswith('replace-with-'):
    raise RuntimeError('JWT_SECRET must contain at least 32 characters.')
