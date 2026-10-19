import logging
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from sqlalchemy.ext.asyncio import AsyncSession

from bookit.db.models import Service
from bookit.repositories import ServiceRepository
from bookit.services.exceptions import ServiceNotFoundError, ValidationError

logger = logging.getLogger(__name__)

NAME_MAX_LENGTH = 100
MIN_DURATION = 5
MAX_DURATION = 480
MAX_PRICE = Decimal("1000000")


def parse_duration(text: str) -> int:
    try:
        value = int(text.strip())
    except ValueError:
        raise ValidationError("validation.duration_not_int") from None
    return validate_duration(value)


def validate_duration(value: int) -> int:
    if not MIN_DURATION <= value <= MAX_DURATION:
        raise ValidationError("validation.duration_range", min=MIN_DURATION, max=MAX_DURATION)
    return value


def parse_price(text: str) -> Decimal:
    normalized = text.strip().replace("₽", "").replace(" ", "").replace(",", ".")
    try:
        value = Decimal(normalized)
    except InvalidOperation:
        raise ValidationError("validation.price_not_number") from None
    return validate_price(value)


def validate_price(value: Decimal) -> Decimal:
    if not value.is_finite() or value < 0 or value > MAX_PRICE:
        raise ValidationError("validation.price_range", max=MAX_PRICE)
    if value != value.quantize(Decimal("0.01")):
        raise ValidationError("validation.price_precision")
    return value.quantize(Decimal("0.01"))


def validate_name(text: str) -> str:
    name = " ".join(text.split())
    if not name:
        raise ValidationError("validation.name_empty")
    if len(name) > NAME_MAX_LENGTH:
        raise ValidationError("validation.name_too_long", max=NAME_MAX_LENGTH)
    return name


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._services = ServiceRepository(session)

    async def list_active(self) -> Sequence[Service]:
        return await self._services.list(only_active=True)

    async def list_all(self) -> Sequence[Service]:
        return await self._services.list(only_active=False)

    async def get(self, service_id: int) -> Service:
        service = await self._services.get(service_id)
        if service is None:
            raise ServiceNotFoundError
        return service

    async def create(self, name: str, duration_min: int, price: Decimal) -> Service:
        service = Service(
            name=validate_name(name),
            duration_min=validate_duration(duration_min),
            price=validate_price(price),
            is_active=True,
        )
        await self._services.add(service)
        await self._session.commit()
        logger.info("Service added id=%s %r", service.id, service.name)
        return service

    async def update_price(self, service_id: int, price: Decimal) -> Service:
        service = await self.get(service_id)
        service.price = validate_price(price)
        await self._session.commit()
        return service

    async def update_duration(self, service_id: int, duration_min: int) -> Service:
        service = await self.get(service_id)
        service.duration_min = validate_duration(duration_min)
        await self._session.commit()
        return service

    async def toggle_active(self, service_id: int) -> Service:
        service = await self.get(service_id)
        service.is_active = not service.is_active
        await self._session.commit()
        logger.info("Service id=%s is_active=%s", service.id, service.is_active)
        return service
