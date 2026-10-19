from aiogram.fsm.state import State, StatesGroup


class BookingFlow(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_slot = State()
    confirming = State()


class AddService(StatesGroup):
    name = State()
    duration = State()
    price = State()


class EditService(StatesGroup):
    price = State()
    duration = State()


class AddDayOff(StatesGroup):
    day = State()
    reason = State()
