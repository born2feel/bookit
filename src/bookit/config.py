from dataclasses import dataclass
from datetime import time
from typing import Annotated, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class DbSettings(BaseSettings):
    """DB settings live separately so that Alembic does not require BOT_TOKEN."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./bookit.db"


class Settings(DbSettings):
    bot_token: SecretStr
    admin_ids: Annotated[frozenset[int], NoDecode] = frozenset()
    timezone: str = "America/New_York"
    work_start: time = time(10, 0)
    work_end: time = time(20, 0)
    slot_step_minutes: int = Field(default=30, ge=5, le=240)
    booking_horizon_days: int = Field(default=14, ge=1, le=60)
    log_level: str = "INFO"

    @field_validator("bot_token")
    @classmethod
    def _check_token(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("BOT_TOKEN is not set")
        return value

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> object:
        if isinstance(value, str):
            return frozenset(int(part) for part in value.split(",") if part.strip())
        if isinstance(value, int):
            return frozenset({value})
        return value

    @field_validator("timezone")
    @classmethod
    def _check_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError(f"Unknown timezone: {value}") from None
        return value

    @model_validator(mode="after")
    def _check_working_hours(self) -> Self:
        if self.work_end <= self.work_start:
            raise ValueError("WORK_END must be later than WORK_START")
        return self

    def schedule_config(self) -> "ScheduleConfig":
        return ScheduleConfig(
            tz=ZoneInfo(self.timezone),
            work_start=self.work_start,
            work_end=self.work_end,
            slot_step_minutes=self.slot_step_minutes,
            horizon_days=self.booking_horizon_days,
        )


@dataclass(frozen=True, slots=True)
class ScheduleConfig:
    """Schedule parameters needed by the services layer (independent of env)."""

    tz: ZoneInfo
    work_start: time
    work_end: time
    slot_step_minutes: int
    horizon_days: int
