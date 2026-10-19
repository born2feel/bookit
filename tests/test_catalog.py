from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bookit.db.models import Service
from bookit.services import CatalogService
from bookit.services.catalog import parse_duration, parse_price, validate_name
from bookit.services.exceptions import ServiceNotFoundError, ValidationError


class TestParsing:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("1500", Decimal("1500.00")),
            ("1 499,90 ₽", Decimal("1499.90")),
            ("0", Decimal("0.00")),
            (" 99.5 ", Decimal("99.50")),
        ],
    )
    def test_valid_price(self, text: str, expected: Decimal) -> None:
        assert parse_price(text) == expected

    @pytest.mark.parametrize("text", ["abc", "", "-1", "1.999", "NaN", "Infinity", "2000000"])
    def test_invalid_price(self, text: str) -> None:
        with pytest.raises(ValidationError):
            parse_price(text)

    def test_valid_duration(self) -> None:
        assert parse_duration(" 60 ") == 60

    @pytest.mark.parametrize("text", ["4", "481", "abc", "1.5", ""])
    def test_invalid_duration(self, text: str) -> None:
        with pytest.raises(ValidationError):
            parse_duration(text)

    def test_name_is_normalized(self) -> None:
        assert validate_name("  Men's   haircut ") == "Men's haircut"

    @pytest.mark.parametrize("text", ["", "   ", "x" * 101])
    def test_invalid_name(self, text: str) -> None:
        with pytest.raises(ValidationError):
            validate_name(text)


class TestCatalogService:
    async def test_create_and_get(self, session: AsyncSession) -> None:
        catalog = CatalogService(session)

        created = await catalog.create(" Haircut ", 60, Decimal("1500"))
        fetched = await catalog.get(created.id)

        assert fetched.name == "Haircut"
        assert fetched.price == Decimal("1500.00")
        assert fetched.is_active

    async def test_create_validates_values(self, session: AsyncSession) -> None:
        with pytest.raises(ValidationError):
            await CatalogService(session).create("Haircut", 1000, Decimal("1500"))

    async def test_hidden_service_is_not_in_active_list(
        self, session: AsyncSession, haircut: Service, beard: Service
    ) -> None:
        catalog = CatalogService(session)

        toggled = await catalog.toggle_active(haircut.id)

        assert not toggled.is_active
        assert [s.id for s in await catalog.list_active()] == [beard.id]
        assert {s.id for s in await catalog.list_all()} == {haircut.id, beard.id}

    async def test_toggle_twice_restores_service(
        self, session: AsyncSession, haircut: Service
    ) -> None:
        catalog = CatalogService(session)
        await catalog.toggle_active(haircut.id)

        restored = await catalog.toggle_active(haircut.id)

        assert restored.is_active

    async def test_update_price_and_duration(self, session: AsyncSession, haircut: Service) -> None:
        catalog = CatalogService(session)

        await catalog.update_price(haircut.id, Decimal("1800"))
        updated = await catalog.update_duration(haircut.id, 45)

        assert updated.price == Decimal("1800.00")
        assert updated.duration_min == 45

    async def test_missing_service(self, session: AsyncSession) -> None:
        with pytest.raises(ServiceNotFoundError):
            await CatalogService(session).update_price(999, Decimal("1"))
