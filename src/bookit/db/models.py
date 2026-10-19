from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import BigInteger, Date, Enum, ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bookit.db.base import Base, UTCDateTime, utcnow


class BookingStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class Language(StrEnum):
    RU = "ru"
    EN = "en"


DEFAULT_LANGUAGE = Language.RU


def _str_enum(enum: type[StrEnum]) -> Enum:
    """Store the enum as VARCHAR rather than a native PostgreSQL type — easier migrations."""
    return Enum(
        enum,
        native_enum=False,
        length=16,
        values_callable=lambda members: [member.value for member in members],
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(64))
    language: Mapped[Language] = mapped_column(
        _str_enum(Language), default=DEFAULT_LANGUAGE, server_default=DEFAULT_LANGUAGE.value
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    duration_min: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        # Database-level guard against double booking:
        # two active bookings cannot share the same start time.
        Index(
            "uq_bookings_active_start_at",
            "start_at",
            unique=True,
            sqlite_where=text("status = 'active'"),
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_bookings_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    start_at: Mapped[datetime] = mapped_column(UTCDateTime())
    end_at: Mapped[datetime] = mapped_column(UTCDateTime())
    status: Mapped[BookingStatus] = mapped_column(
        _str_enum(BookingStatus), default=BookingStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    user: Mapped[User] = relationship(lazy="joined")
    service: Mapped[Service] = relationship(lazy="joined")


class DayOff(Base):
    __tablename__ = "days_off"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(Date, unique=True)
    reason: Mapped[str | None] = mapped_column(String(255))
