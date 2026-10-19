class BookItError(Exception):
    """Base domain error.

    The services layer knows nothing about the user's language: an error carries
    a translation key and parameters, and the bot layer renders the text.
    """

    key = "error.generic"

    def __init__(self, key: str | None = None, **params: object) -> None:
        self.key = key or type(self).key
        self.params = params
        super().__init__(self.key)


class ValidationError(BookItError):
    key = "validation.generic"


class ServiceNotFoundError(BookItError):
    key = "error.service_not_found"


class ServiceInactiveError(BookItError):
    key = "error.service_inactive"


class DateUnavailableError(BookItError):
    key = "error.date_unavailable"


class SlotUnavailableError(BookItError):
    key = "error.slot_unavailable"


class BookingNotFoundError(BookItError):
    key = "error.booking_not_found"


class BookingAlreadyCancelledError(BookItError):
    key = "error.booking_already_cancelled"


class BookingInPastError(BookItError):
    key = "error.booking_in_past"


class DayOffExistsError(BookItError):
    key = "error.day_off_exists"


class DayOffNotFoundError(BookItError):
    key = "error.day_off_not_found"


class DayHasBookingsError(BookItError):
    key = "error.day_has_bookings"

    def __init__(self, count: int) -> None:
        self.count = count
        super().__init__(count=count)
