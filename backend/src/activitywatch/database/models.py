import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    Text,
    JSON,
    ForeignKey,
    UniqueConstraint,
    Index,
    text,
    Enum,
    LargeBinary,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
    Session,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
import enum


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""

    __abstract__ = True

    def to_dict(self, exclude: List[str] = None) -> Dict[str, Any]:
        """Конвертирует модель в словарь"""
        if exclude is None:
            exclude = []

        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                # Конвертируем специальные типы
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    value = str(value)
                result[column.name] = value

        return result

    def update(self, **kwargs):
        """Обновляет атрибуты модели"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def get(cls, session: Session, id: Any):
        """Получить объект по ID"""
        return session.get(cls, id)


# Enums
class DevicePlatform(str, enum.Enum):
    """Платформы устройств"""

    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    ANDROID = "android"
    IOS = "ios"
    OTHER = "other"


class SyncStatus(str, enum.Enum):
    """Статусы синхронизации"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"


class TokenPermission(str, enum.Enum):
    """Разрешения для токенов"""

    READ_ACTIVITY = "read:activity"
    WRITE_ACTIVITY = "write:activity"
    READ_PROFILE = "read:profile"
    WRITE_PROFILE = "write:profile"
    MANAGE_DEVICES = "manage:devices"
    ADMIN = "admin"


# Модели
class User(Base):
    """Пользователи системы"""

    __tablename__ = "users"
    __table_args__ = {"comment": "Пользователи системы ActivityWatch Sync"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Идентификатор пользователя",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Email пользователя (уникальный)",
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="Имя пользователя (опционально)",
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Хэш пароля (если используется локальная аутентификация)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Активен ли пользователь"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Подтвержден ли email"
    )
    settings: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="Настройки пользователя в формате JSON",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        comment="Дата создания",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        comment="Дата последнего обновления",
    )

    # Relationships
    devices: Mapped[List["Device"]] = relationship(
        "Device", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    tokens: Mapped[List["ApiToken"]] = relationship(
        "ApiToken", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    @validates("email")
    def validate_email(self, key: str, value: str) -> str:
        """Валидация email"""
        if "@" not in value:
            raise ValueError("Invalid email address")
        return value.lower()

    @hybrid_property
    def devices_count(self) -> int:
        """Количество устройств пользователя"""
        return len(self.devices) if self.devices else 0


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="uq_user_device"),
        {"comment": "Устройства пользователей для синхронизации"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(String(255), nullable=True, comment="Уникальный UUID устройства")
    device_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Unnamed Device")
    platform: Mapped[DevicePlatform] = mapped_column(Enum(DevicePlatform, native_enum=False), nullable=False, default=DevicePlatform.OTHER)
    platform_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    platform_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Unnamed Device")
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    system: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # ✅ НОВЫЕ ПОЛЯ из клиента
    client_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="Версия клиентского ПО")
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="devices", lazy="joined")
    tokens: Mapped[List["ApiToken"]] = relationship(
        "ApiToken",
        back_populates="device",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    sync_sessions: Mapped[List["SyncSession"]] = relationship(
        "SyncSession",
        back_populates="device",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    activity_events: Mapped[List["ActivityEvent"]] = relationship(
        "ActivityEvent",
        back_populates="device",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def update_last_seen(self):
        """Обновляет время последней активности"""
        self.last_seen = datetime.now(timezone.utc)


class ApiToken(Base):
    """API токены для аутентификации устройств"""

    __tablename__ = "api_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", "device_id", "name", name="uq_token_name"),
        Index("ix_tokens_token_hash", "token_hash"),
        {"comment": "API токены для аутентификации устройств"},
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="Идентификатор токена"
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID пользователя",
    )
    device_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="ID устройства",
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Хэш токена (никогда не храним сам токен!)",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Название токена (например, 'Основной токен')",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        comment="Дата создания",
    )
 
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tokens", lazy="joined")
    device: Mapped["Device"] = relationship(
        "Device", back_populates="tokens", lazy="joined"
    )
    sync_sessions: Mapped[List["SyncSession"]] = relationship(
        "SyncSession", back_populates="token", lazy="selectin"
    )

    @validates("permissions")
    def validate_permissions(self, key: str, value: List[str]) -> List[str]:
        """Валидация разрешений"""
        valid_permissions = [p.value for p in TokenPermission]
        for perm in value:
            if perm not in valid_permissions:
                raise ValueError(f"Invalid permission: {perm}")
        return value

    @hybrid_property
    def is_expired(self) -> bool:
        """Проверяет, истек ли срок действия токена"""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.now(timezone.utc)


class SyncSession(Base):
    """Сессии синхронизации"""

    __tablename__ = "sync_sessions"
    __table_args__ = (
        Index("ix_sync_sessions_device_time", "device_id", "start_time"),
        {"comment": "Сессии синхронизации данных"},
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="Идентификатор сессии"
    )
    device_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID устройства",
    )
    token_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("api_tokens.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID использованного токена",
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        comment="Время начала синхронизации",
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Время окончания синхронизации"
    )
    events_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Количество обработанных событий"
    )
    status: Mapped[SyncStatus] = mapped_column(
        Enum(SyncStatus, native_enum=False),
        nullable=False,
        default=SyncStatus.PENDING,
        comment="Статус синхронизации",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Сообщение об ошибке (если есть)"
    )
    meta_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="Дополнительная информация о сессии",
    )

    # Relationships
    device: Mapped["Device"] = relationship(
        "Device", back_populates="sync_sessions", lazy="joined"
    )
    token: Mapped[Optional["ApiToken"]] = relationship(
        "ApiToken", back_populates="sync_sessions", lazy="joined"
    )
    activity_events: Mapped[List["ActivityEvent"]] = relationship(
        "ActivityEvent",
        back_populates="sync_session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @hybrid_property
    def duration(self) -> Optional[float]:
        """Длительность сессии в секундах"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def complete(self, status: SyncStatus, error_message: str = None):
        """Завершает сессию синхронизации"""
        self.end_time = datetime.now(timezone.utc)
        self.status = status
        if error_message:
            self.error_message = error_message


class ActivityEvent(Base):
    """События активности"""

    __tablename__ = "activity_events"
    __table_args__ = (
        Index("ix_events_device_time", "device_id", "timestamp"),
        Index("ix_events_app", "app"),
        UniqueConstraint("device_id", "event_id", "timestamp", name="uq_event_unique"),
        {"comment": "События активности пользователей"},
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="Идентификатор события"
    )
    device_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID устройства",
    )
    sync_session_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sync_sessions.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID сессии синхронизации",
    )
    event_id: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Уникальный ID события из ActivityWatch"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, comment="Время события"
    )
    duration_seconds: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Длительность события в секундах"
    )
    app: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Название приложения"
    )
    window_title: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Заголовок окна"
    )
    url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="URL (для браузеров)"
    )
    data: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="Полные данные события в формате JSON",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        comment="Время создания записи в БД",
    )

    # Relationships
    device: Mapped["Device"] = relationship(
        "Device", back_populates="activity_events", lazy="joined"
    )
    sync_session: Mapped[Optional["SyncSession"]] = relationship(
        "SyncSession", back_populates="activity_events", lazy="joined"
    )

    @hybrid_property
    def duration_minutes(self) -> float:
        """Длительность события в минутах"""
        return self.duration_seconds / 60

    @hybrid_property
    def duration_hours(self) -> float:
        """Длительность события в часах"""
        return self.duration_seconds / 3600


__all__ = [
    "Base",
    "User",
    "Device",
    "ApiToken",
    "SyncSession",
    "ActivityEvent",
    "DevicePlatform",
    "SyncStatus",
    "TokenPermission",
]
