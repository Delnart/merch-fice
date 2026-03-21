from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🛍 Каталог", callback_data="catalog:view")
    b.button(text="🛒 Мій кошик", callback_data="cart:view")
    b.adjust(2)
    return b.as_markup()

def catalog_keyboard(products: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for product_id, title in products:
        b.button(text=title, callback_data=f"product:{product_id}")
    b.button(text="🔙 На головну", callback_data="menu:main")
    b.adjust(1)
    return b.as_markup()

def sizes_keyboard(product_id: int, sizes: list[str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for size in sizes:
        b.button(text=f"Додати {size}", callback_data=f"cart:add:{product_id}:{size}")
    b.button(text="🔙 До каталогу", callback_data="catalog:view")
    b.adjust(2, 1)
    return b.as_markup()

def cart_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Оформити замовлення", callback_data="checkout:start")
    b.button(text="🗑 Очистити кошик", callback_data="cart:clear")
    b.button(text="🔙 На головну", callback_data="menu:main")
    b.adjust(1)
    return b.as_markup()

def admin_main_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Додати товар", callback_data="admin:add_product")
    b.button(text="📦 Усі товари", callback_data="admin:products")
    b.button(text="💳 Лінк на Банку", callback_data="admin:set_mono")
    b.button(text="📝 Текст привітання", callback_data="admin:set_welcome")
    b.adjust(2)
    return b.as_markup()

def admin_product_item_keyboard(product_id: int, is_active: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    status_text = "🔴 Архівувати" if is_active else "🟢 Активувати"
    b.button(text=status_text, callback_data=f"admin:toggle:{product_id}")
    b.button(text="🔙 Назад", callback_data="admin:products")
    b.adjust(1)
    return b.as_markup()

def order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔄 В роботу", callback_data=f"ostatus:{order_id}:in_process")
    b.button(text="✅ Виконано", callback_data=f"ostatus:{order_id}:completed")
    b.button(text="❌ Скасовано", callback_data=f"ostatus:{order_id}:cancelled")
    b.adjust(2, 1)
    return b.as_markup()