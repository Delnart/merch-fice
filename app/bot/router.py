from decimal import Decimal

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import cart_keyboard, catalog_keyboard, order_status_keyboard, sizes_keyboard
from app.bot.states import AdminProductPhotoState, CheckoutState
from app.db.models import OrderStatus
from app.db.session import AsyncSessionLocal
from app.services.admin_config import bind_admin_chat, get_active_admin_binding, get_or_create_shop_config
from app.services.auth import is_chat_admin, is_group_chat
from app.services.cart import add_to_cart, clear_cart, ensure_user, list_cart
from app.services.catalog import (
    archive_product,
    create_product,
    get_product,
    get_sizes,
    list_active_products,
    list_all_products,
    replace_sizes,
    set_product_description,
    set_product_photo,
    set_size_price,
)
from app.services.orders import create_order_from_cart, get_order, set_order_admin_message, set_order_status
from app.services.parsers import parse_sizes_map, split_command_payload, split_pipe_payload


router = Router()


async def require_admin_group(message: Message, bot: Bot) -> bool:
    if message.chat is None or message.from_user is None:
        return False
    async with AsyncSessionLocal() as session:
        binding = await get_active_admin_binding(session)
    if binding is None:
        return False
    if message.chat.id != binding.chat_id:
        return False
    return await is_chat_admin(bot, message.chat.id, message.from_user.id)


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    if message.from_user is None:
        return
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await ensure_user(
                session,
                message.from_user.id,
                message.from_user.username,
                message.from_user.first_name,
                message.from_user.last_name,
            )
            config = await get_or_create_shop_config(session)
    if message.chat.type == "private":
        await message.answer(config.welcome_text)
        await message.answer("Використайте /catalog щоб переглянути товари")


@router.message(Command("bind_admin_chat"))
async def bind_admin_chat_handler(message: Message, bot: Bot) -> None:
    if message.chat is None or message.from_user is None:
        return
    if not is_group_chat(message.chat.type):
        await message.answer("Ця команда працює лише в групі")
        return
    if not await is_chat_admin(bot, message.chat.id, message.from_user.id):
        await message.answer("Тільки Telegram-admin цього чату може прив'язати адмінку")
        return
    async with AsyncSessionLocal() as session:
        async with session.begin():
            binding = await bind_admin_chat(session, message.chat.id, message.chat.title or "Admin Chat")
            config = await get_or_create_shop_config(session)
    sent = await message.answer(
        f"Адмін-чат прив'язано\nЧат: {binding.title}\nВалюта: {config.currency}\nКоманди: /add_product /set_sizes /set_price /set_text /set_photo /products"
    )
    try:
        await bot.pin_chat_message(chat_id=message.chat.id, message_id=sent.message_id, disable_notification=True)
    except Exception:
        pass
    async with AsyncSessionLocal() as session:
        async with session.begin():
            active = await get_active_admin_binding(session)
            if active is not None:
                active.pinned_config_message_id = sent.message_id


@router.message(Command("products"))
async def products_handler(message: Message, bot: Bot) -> None:
    if not await require_admin_group(message, bot):
        return
    async with AsyncSessionLocal() as session:
        items = await list_all_products(session)
    if not items:
        await message.answer("Товарів ще немає")
        return
    lines = []
    for item in items:
        status = "active" if item.is_active else "archived"
        lines.append(f"#{item.id} {item.title} [{status}]")
    await message.answer("\n".join(lines))


@router.message(Command("add_product"))
async def add_product_handler(message: Message, bot: Bot) -> None:
    if not await require_admin_group(message, bot):
        return
    payload = split_command_payload(message.text or "")
    try:
        title, description = split_pipe_payload(payload, 2)
    except ValueError:
        await message.answer("Формат: /add_product Назва | Опис")
        return

    async with AsyncSessionLocal() as session:
        async with session.begin():
            product = await create_product(session, title=title, description=description)
    await message.answer(f"Створено товар #{product.id}")


@router.message(Command("set_sizes"))
async def set_sizes_handler(message: Message, bot: Bot) -> None:
    if not await require_admin_group(message, bot):
        return
    payload = split_command_payload(message.text or "")
    try:
        product_id_raw, sizes_raw = split_pipe_payload(payload, 2)
        product_id = int(product_id_raw)
        sizes = parse_sizes_map(sizes_raw)
    except Exception:
        await message.answer("Формат: /set_sizes product_id | S:500,M:550,L:600")
        return

    async with AsyncSessionLocal() as session:
        async with session.begin():
            product = await get_product(session, product_id)
            if product is None:
                await message.answer("Товар не знайдено")
                return
            await replace_sizes(session, product, sizes)
    await message.answer("Розміри та ціни оновлено")


@router.message(Command("set_price"))
async def set_price_handler(message: Message, bot: Bot) -> None:
    if not await require_admin_group(message, bot):
        return
    payload = split_command_payload(message.text or "")
    try:
        product_id_raw, size, price_raw = split_pipe_payload(payload, 3)
        product_id = int(product_id_raw)
        price = float(price_raw)
    except Exception:
        await message.answer("Формат: /set_price product_id | SIZE | 500")
        return

    async with AsyncSessionLocal() as session:
        async with session.begin():
            product = await get_product(session, product_id)
            if product is None:
                await message.answer("Товар не знайдено")
                return
            await set_size_price(session, product, size=size.upper(), price=price)
    await message.answer("Ціну оновлено")


@router.message(Command("set_text"))
async def set_text_handler(message: Message, bot: Bot) -> None:
    if not await require_admin_group(message, bot):
        return
    payload = split_command_payload(message.text or "")
    try:
        product_id_raw, description = split_pipe_payload(payload, 2)
        product_id = int(product_id_raw)
    except Exception:
        await message.answer("Формат: /set_text product_id | Новий опис")
        return

    async with AsyncSessionLocal() as session:
        async with session.begin():
            product = await get_product(session, product_id)
            if product is None:
                await message.answer("Товар не знайдено")
                return
            await set_product_description(session, product, description)
    await message.answer("Опис оновлено")


@router.message(Command("set_photo"))
async def set_photo_handler(message: Message, bot: Bot, state: FSMContext) -> None:
    if not await require_admin_group(message, bot):
        return
    payload = split_command_payload(message.text or "")
    try:
        product_id = int(payload)
    except Exception:
        await message.answer("Формат: /set_photo product_id")
        return
    async with AsyncSessionLocal() as session:
        product = await get_product(session, product_id)
    if product is None:
        await message.answer("Товар не знайдено")
        return
    await state.set_state(AdminProductPhotoState.waiting_photo)
    await state.update_data(product_id=product_id)
    await message.answer("Надішліть фото наступним повідомленням")


@router.message(AdminProductPhotoState.waiting_photo, F.photo)
async def receive_photo_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    if not await require_admin_group(message, bot):
        await state.clear()
        return
    data = await state.get_data()
    product_id = data.get("product_id")
    if not product_id:
        await state.clear()
        return
    photo = message.photo[-1]
    async with AsyncSessionLocal() as session:
        async with session.begin():
            product = await get_product(session, int(product_id))
            if product is None:
                await message.answer("Товар не знайдено")
                await state.clear()
                return
            await set_product_photo(session, product, photo.file_id)
    await message.answer("Фото оновлено")
    await state.clear()


@router.message(Command("archive_product"))
async def archive_handler(message: Message, bot: Bot) -> None:
    if not await require_admin_group(message, bot):
        return
    payload = split_command_payload(message.text or "")
    try:
        product_id = int(payload)
    except Exception:
        await message.answer("Формат: /archive_product product_id")
        return
    async with AsyncSessionLocal() as session:
        async with session.begin():
            product = await get_product(session, product_id)
            if product is None:
                await message.answer("Товар не знайдено")
                return
            await archive_product(session, product, is_active=False)
    await message.answer("Товар архівовано")


@router.message(Command("unarchive_product"))
async def unarchive_handler(message: Message, bot: Bot) -> None:
    if not await require_admin_group(message, bot):
        return
    payload = split_command_payload(message.text or "")
    try:
        product_id = int(payload)
    except Exception:
        await message.answer("Формат: /unarchive_product product_id")
        return
    async with AsyncSessionLocal() as session:
        async with session.begin():
            product = await get_product(session, product_id)
            if product is None:
                await message.answer("Товар не знайдено")
                return
            await archive_product(session, product, is_active=True)
    await message.answer("Товар активовано")


@router.message(Command("set_welcome"))
async def set_welcome_handler(message: Message, bot: Bot) -> None:
    if not await require_admin_group(message, bot):
        return
    payload = split_command_payload(message.text or "")
    if not payload:
        await message.answer("Формат: /set_welcome Текст")
        return
    async with AsyncSessionLocal() as session:
        async with session.begin():
            config = await get_or_create_shop_config(session)
            config.welcome_text = payload
    await message.answer("Текст привітання оновлено")


@router.message(Command("catalog"))
async def catalog_handler(message: Message) -> None:
    if message.chat.type != "private":
        return
    async with AsyncSessionLocal() as session:
        products = await list_active_products(session)
    if not products:
        await message.answer("Зараз немає доступних товарів")
        return
    pairs = [(item.id, item.title) for item in products]
    await message.answer("Оберіть товар", reply_markup=catalog_keyboard(pairs))


@router.callback_query(F.data == "catalog:back")
async def catalog_back_handler(callback: CallbackQuery) -> None:
    if callback.message is None:
        return
    async with AsyncSessionLocal() as session:
        products = await list_active_products(session)
    if not products:
        await callback.message.edit_text("Зараз немає доступних товарів")
        await callback.answer()
        return
    await callback.message.edit_text(
        "Оберіть товар",
        reply_markup=catalog_keyboard([(item.id, item.title) for item in products]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def product_view_handler(callback: CallbackQuery) -> None:
    if callback.message is None:
        return
    product_id = int(callback.data.split(":", maxsplit=1)[1])
    async with AsyncSessionLocal() as session:
        product = await get_product(session, product_id)
        sizes = await get_sizes(session, product_id)
    if product is None or not product.is_active:
        await callback.answer("Товар недоступний", show_alert=True)
        return
    if not sizes:
        await callback.answer("Розміри ще не налаштовані", show_alert=True)
        return
    text = f"{product.title}\n\n{product.description}\n\n" + "\n".join([f"{s.size}: {Decimal(s.price)}" for s in sizes])
    keyboard = sizes_keyboard(product_id, [s.size for s in sizes])
    if product.photo_file_id:
        await callback.message.answer_photo(photo=product.photo_file_id, caption=text, reply_markup=keyboard)
    else:
        await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("cart:add:"))
async def cart_add_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        return
    _, _, product_id_raw, size = callback.data.split(":")
    product_id = int(product_id_raw)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await ensure_user(
                session,
                callback.from_user.id,
                callback.from_user.username,
                callback.from_user.first_name,
                callback.from_user.last_name,
            )
            try:
                await add_to_cart(session, callback.from_user.id, product_id=product_id, size=size, quantity=1)
            except ValueError:
                await callback.answer("Розмір недоступний", show_alert=True)
                return
    await callback.answer("Додано в кошик")


@router.callback_query(F.data == "cart:view")
async def cart_view_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        return
    async with AsyncSessionLocal() as session:
        rows = await list_cart(session, callback.from_user.id)
    if not rows:
        await callback.message.answer("Кошик порожній")
        await callback.answer()
        return
    total = Decimal("0")
    lines = []
    for item, product in rows:
        line_total = Decimal(str(item.price)) * item.quantity
        total += line_total
        lines.append(f"{product.title} | {item.size} | {item.quantity} x {Decimal(item.price)} = {line_total}")
    lines.append(f"Разом: {total}")
    await callback.message.answer("\n".join(lines), reply_markup=cart_keyboard())
    await callback.answer()


@router.message(Command("cart"))
async def cart_command_handler(message: Message) -> None:
    if message.chat.type != "private" or message.from_user is None:
        return
    async with AsyncSessionLocal() as session:
        rows = await list_cart(session, message.from_user.id)
    if not rows:
        await message.answer("Кошик порожній")
        return
    total = Decimal("0")
    lines = []
    for item, product in rows:
        line_total = Decimal(str(item.price)) * item.quantity
        total += line_total
        lines.append(f"{product.title} | {item.size} | {item.quantity} x {Decimal(item.price)} = {line_total}")
    lines.append(f"Разом: {total}")
    await message.answer("\n".join(lines), reply_markup=cart_keyboard())


@router.callback_query(F.data == "cart:clear")
async def cart_clear_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        return
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await clear_cart(session, callback.from_user.id)
    await callback.answer("Кошик очищено")


@router.callback_query(F.data == "checkout:start")
async def checkout_start_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return
    async with AsyncSessionLocal() as session:
        rows = await list_cart(session, callback.from_user.id)
    if not rows:
        await callback.answer("Кошик порожній", show_alert=True)
        return
    await state.set_state(CheckoutState.waiting_payment_method)
    await callback.message.answer("Вкажіть спосіб оплати")
    await callback.answer()


@router.message(CheckoutState.waiting_payment_method)
async def checkout_payment_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(payment_method=message.text or "")
    await state.set_state(CheckoutState.waiting_phone)
    await message.answer("Вкажіть номер телефону")


@router.message(CheckoutState.waiting_phone)
async def checkout_phone_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text or "")
    await state.set_state(CheckoutState.waiting_address)
    await message.answer("Вкажіть адресу доставки")


@router.message(CheckoutState.waiting_address)
async def checkout_address_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(address=message.text or "")
    await state.set_state(CheckoutState.waiting_note)
    await message.answer("Коментар до замовлення або '-' без коментаря")


@router.message(CheckoutState.waiting_note)
async def checkout_note_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.from_user is None:
        await state.clear()
        return
    data = await state.get_data()
    note = None if (message.text or "").strip() == "-" else (message.text or "").strip()
    async with AsyncSessionLocal() as session:
        async with session.begin():
            config = await get_or_create_shop_config(session)
            order = await create_order_from_cart(
                session,
                telegram_id=message.from_user.id,
                payment_method=data.get("payment_method", ""),
                phone=data.get("phone", ""),
                address=data.get("address", ""),
                note=note,
                currency=config.currency,
            )
            binding = await get_active_admin_binding(session)
            await session.refresh(order)
            await session.refresh(order, attribute_names=["items"])

    await message.answer(f"Замовлення #{order.id} створено. Статус: {order.status.value}")

    if binding is not None:
        lines = [
            f"Нове замовлення #{order.id}",
            f"Клієнт: @{message.from_user.username or 'user'} ({message.from_user.id})",
            f"Телефон: {data.get('phone', '')}",
            f"Адреса: {data.get('address', '')}",
            f"Оплата: {data.get('payment_method', '')}",
            f"Сума: {Decimal(order.total_amount)} {order.currency}",
            "Позиції:",
        ]
        for item in order.items:
            lines.append(f"- {item.title} | {item.size} | {item.quantity} x {Decimal(item.unit_price)}")
        if note:
            lines.append(f"Коментар: {note}")
        sent = await bot.send_message(binding.chat_id, "\n".join(lines), reply_markup=order_status_keyboard(order.id))
        async with AsyncSessionLocal() as session:
            async with session.begin():
                db_order = await get_order(session, order.id)
                if db_order is not None:
                    await set_order_admin_message(session, db_order, sent.message_id)

    await state.clear()


@router.callback_query(F.data.startswith("orderstatus:"))
async def order_status_handler(callback: CallbackQuery, bot: Bot) -> None:
    if callback.message is None or callback.from_user is None:
        return
    if callback.message.chat.type not in {"group", "supergroup"}:
        await callback.answer()
        return
    if not await is_chat_admin(bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("Недостатньо прав", show_alert=True)
        return

    _, order_id_raw, status_raw = callback.data.split(":")
    order_id = int(order_id_raw)
    status = OrderStatus(status_raw)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            binding = await get_active_admin_binding(session)
            if binding is None or binding.chat_id != callback.message.chat.id:
                await callback.answer("Це не активна адмінка", show_alert=True)
                return
            order = await get_order(session, order_id)
            if order is None:
                await callback.answer("Замовлення не знайдено", show_alert=True)
                return
            await set_order_status(session, order, status)
            user_id = order.telegram_id

    await callback.answer("Статус оновлено")
    await callback.message.edit_reply_markup(reply_markup=order_status_keyboard(order_id))
    try:
        await bot.send_message(user_id, f"Статус замовлення #{order_id}: {status.value}")
    except Exception:
        pass


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp
