from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from bookit.config import ScheduleConfig
from bookit.db.base import Base
from bookit.db.models import Service, User
from bookit.services import CatalogService, UserService

TZ = ZoneInfo("America/New_York")
TODAY = date(2026, 10, 19)  # Monday
# 08:00 New York time — the working day has not started yet
NOW = datetime.combine(TODAY, time(8, 0), tzinfo=TZ).astimezone(UTC)


def at(day: date, hour: int, minute: int = 0) -> datetime:
    """Local (New York) time → aware datetime."""
    return datetime.combine(day, time(hour, minute), tzinfo=TZ)


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def cfg() -> ScheduleConfig:
    return ScheduleConfig(
        tz=TZ,
        work_start=time(10, 0),
        work_end=time(18, 0),
        slot_step_minutes=30,
        horizon_days=14,
    )


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    async with sessionmaker() as db_session:
        yield db_session
    await engine.dispose()


@pytest.fixture
async def user(session: AsyncSession) -> User:
    return await UserService(session).register(tg_id=1001, full_name="Ivan", username="ivan")


@pytest.fixture
async def other_user(session: AsyncSession) -> User:
    return await UserService(session).register(tg_id=1002, full_name="Maria", username=None)


@pytest.fixture
async def haircut(session: AsyncSession) -> Service:
    return await CatalogService(session).create("Haircut", 60, Decimal("35"))


@pytest.fixture
async def beard(session: AsyncSession) -> Service:
    return await CatalogService(session).create("Beard trim", 30, Decimal("15"))
