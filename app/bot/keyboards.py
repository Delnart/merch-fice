from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def catalog_keyboard(products: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=title, callback_data=f"product:{product_id}")] for product_id, title in products]
    rows.append([InlineKeyboardButton(text="Кошик", callback_data="cart:view")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def sizes_keyboard(product_id: int, sizes: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=size, callback_data=f"cart:add:{product_id}:{size}")] for size in sizes]
    rows.append([InlineKeyboardButton(text="Назад", callback_data="catalog:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оформити", callback_data="checkout:start")],
            [InlineKeyboardButton(text="Очистити кошик", callback_data="cart:clear")],
        ]
    )


def order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="В роботу", callback_data=f"orderstatus:{order_id}:in_process")],
            [InlineKeyboardButton(text="Виконано", callback_data=f"orderstatus:{order_id}:completed")],
            [InlineKeyboardButton(text="Скасовано", callback_data=f"orderstatus:{order_id}:cancelled")],
        ]
    )
