from aiogram.fsm.state import State, StatesGroup

class CheckoutState(StatesGroup):
    waiting_contact = State()
    waiting_delivery = State()
    waiting_receipt = State()

class AdminProductState(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_sizes = State()
    waiting_photo = State()

class AdminConfigState(StatesGroup):
    waiting_mono_url = State()
    waiting_welcome_text = State()