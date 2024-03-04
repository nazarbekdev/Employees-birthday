from aiogram.dispatcher.filters.state import State, StatesGroup


class AddEmployee(StatesGroup):
    FirstName = State()
    LastName = State()
    Birthday = State()
    Position = State()
    Photo = State()
