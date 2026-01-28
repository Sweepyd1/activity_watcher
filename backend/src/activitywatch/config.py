import os
import json
from pathlib import Path
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str = "activitywatch"
    user: str = "postgres"
    password: str = ""
    echo: bool = False
    pool_size: int = 20
    max_overflow: int = 40
    pool_timeout: int = 30
    
    @property
    def url(self) -> str:
        """URL для подключения к PostgreSQL"""
        encoded_password = quote_plus(self.password)
        return f"postgresql://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_url(self) -> str:
        """Async URL для подключения к PostgreSQL"""
        encoded_password = quote_plus(self.password)
        return f"postgresql+asyncpg://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}"


class AppConfig(BaseModel):
    env: str = "development"
    name: str = "ActivityWatch Sync Server"
    version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = ""
    cors_origins: List[str] = ["http://localhost:3000"]
    
    @field_validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        """Проверяем, что секретный ключ установлен в production"""
        if cls.model_fields["env"].default == "production" and not v:
            raise ValueError("SECRET_KEY must be set in production")
        return v
    
    @field_validator("cors_origins", mode="before")
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Парсим CORS origins из строки JSON или списка"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v.strip() for v in v.split(",")]
        return v


class SecurityConfig(BaseModel):
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    @field_validator("jwt_secret_key")
    def validate_jwt_secret(cls, v: str) -> str:
        """Проверяем JWT секрет"""
        if not v:
            raise ValueError("JWT_SECRET_KEY must be set")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    decode_responses: bool = True
    
    @property
    def url(self) -> str:
        """URL для подключения к Redis"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    retention: str = "30 days"
    folder: Path = Path("logs")
    format: str = "json"  # json, console
    
    @field_validator("folder", mode="before")
    def validate_folder(cls, v: Any) -> Path:
        """Проверяем и создаем папку для логов"""
        if isinstance(v, str):
            v = Path(v)
        v = v.resolve()
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("level")
    def validate_level(cls, v: str) -> str:
        """Проверяем уровень логирования"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v.upper()


class AdminAuthConfig(BaseModel):

    login: str = "admin"
    password: str = "admin123"
    email: str = "admin@activitywatch.local"


class ActivityWatchConfig(BaseModel):

    api_url: str = "http://localhost:5600/api/0"
    sync_interval: int = 300  # 5 минут в секундах
    default_device_name: str = "Unnamed Device"
    max_events_per_request: int = 1000


class EmailConfig(BaseModel):

    host: str = ""
    port: int = 587
    user: str = ""
    password: str = ""
    from_email: str = "noreply@activitywatch.local"
    tls: bool = True
    
    @property
    def enabled(self) -> bool:
        """Проверяем, включена ли отправка email"""
        return bool(self.host and self.user)


class WebhookConfig(BaseModel):
    """Конфигурация вебхуков"""
    url: str = ""
    secret: str = ""
    
    @property
    def enabled(self) -> bool:
        """Проверяем, включены ли вебхуки"""
        return bool(self.url)

class GoogleAuthConfig(BaseModel):
    """Конфигурация Google OAuth2"""
    client_id: str = ""
    client_secret: str = ""
    auth_url: str = "https://accounts.google.com/o/oauth2/auth"
    token_url: str = "https://oauth2.googleapis.com/token"
    user_info_url: str = "https://www.googleapis.com/oauth2/v3/userinfo"
    redirect_uri: str = "http://localhost:8000/auth/google/callback"
    
    @field_validator("client_id", "client_secret")
    def validate_google_keys(cls, v: str) -> str:
        """Проверяем обязательные Google ключи"""
        if not v.strip():
            raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set")
        return v.strip()
    
    @property
    def enabled(self) -> bool:
        """Проверяем, включена ли Google авторизация"""
        return bool(self.client_id and self.client_secret)

class Config(BaseSettings):
    """Основной класс конфигурации"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        case_sensitive=False,
        extra="ignore"
    )
    
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    security: SecurityConfig = SecurityConfig()
    redis: RedisConfig = RedisConfig()
    logging: LoggingConfig = LoggingConfig()
    admin: AdminAuthConfig = AdminAuthConfig()
    activitywatch: ActivityWatchConfig = ActivityWatchConfig()
    email: EmailConfig = EmailConfig()
    webhook: WebhookConfig = WebhookConfig()
    google: GoogleAuthConfig = GoogleAuthConfig()
    
    @property
    def is_development(self) -> bool:
        """Проверяем, что окружение - разработка"""
        return self.app.env.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Проверяем, что окружение - продакшн"""
        return self.app.env.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        """Проверяем, что окружение - тестирование"""
        return self.app.env.lower() == "testing"



cfg = Config()


def get_config() -> Config:
    """Получить глобальную конфигурацию"""
    return cfg

def setup_environment():
    """Настройка окружения на основе конфигурации"""
    os.environ.setdefault("PYTHONPATH", str(Path.cwd()))
    
    if cfg.is_development:
        os.environ.setdefault("PYTHONASYNCIODEBUG", "1")
    
    # Устанавливаем уровень логирования
    import logging as std_logging
    std_logging.basicConfig(
        level=getattr(std_logging, cfg.logging.level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )