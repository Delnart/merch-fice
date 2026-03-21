from aiogram.fsm.state import State, StatesGroup


class AdminProductPhotoState(StatesGroup):
    waiting_photo = State()


class CheckoutState(StatesGroup):
    waiting_payment_method = State()
    waiting_phone = State()
    waiting_address = State()
    waiting_note = State()
