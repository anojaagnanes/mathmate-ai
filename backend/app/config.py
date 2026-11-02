from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'sqlite:///./mathmate.db'
    jwt_secret: str
    frontend_origin: str = 'http://localhost:3000'
    secure_cookies: bool = False
    ai_provider: Literal['mock', 'meta'] = 'mock'
    vision_provider: Literal['default', 'ollama'] = 'default'
    model_api_key: str = ''
    meta_model: str = 'muse-spark-1.3'
    meta_enabled: bool = False
    meta_host: Literal['meta', 'baseten'] = 'meta'
    meta_base_url: str = ''
    baseten_api_key: str = ''
    meta_session_request_limit: int = 10
    meta_request_budget: int = 0
    meta_token_budget: int = 0
    meta_max_output_tokens: int = 800
    meta_usage_db: str = 'meta_usage.db'
    meta_estimated_cost_budget_usd: float = 0
    meta_enabled_until: float = 0


settings = Settings()
if len(settings.jwt_secret) < 32 or settings.jwt_secret.startswith('replace-with-'):
    raise RuntimeError('JWT_SECRET must contain at least 32 characters.')
