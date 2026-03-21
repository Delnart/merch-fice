from decimal import Decimal
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import (
    admin_main_keyboard, admin_product_item_keyboard, cart_keyboard, 
    catalog_keyboard, main_menu_keyboard, order_status_keyboard, sizes_keyboard
)
from app.bot.states import AdminConfigState, AdminProductState, CheckoutState
from app.db.models import OrderStatus
from app.db.session import AsyncSessionLocal
from app.services.admin_config import bind_admin_chat, get_active_admin_binding, get_or_create_shop_config
from app.services.auth import is_chat_admin, is_group_chat
from app.services.cart import add_to_cart, clear_cart, ensure_user, list_cart
from app.services.catalog import (
    archive_product, create_product, get_product, get_sizes,
    list_active_products, list_all_products, replace_sizes, set_product_photo
)
from app.services.orders import create_order_from_cart, get_order, set_order_admin_message, set_order_status
from app.services.parsers import parse_sizes_map

router = Router()

async def check_admin_rights(user_id: int, bot: Bot) -> bool:
    async with AsyncSessionLocal() as session:
        binding = await get_active_admin_binding(session)
    if binding is None:
        return False
    return await is_chat_admin(bot, binding.chat_id, user_id)

@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext) -> None:
    if message.from_user is None or message.chat.type != "private":
        return
    await state.clear()
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await ensure_user(
                session, message.from_user.id, message.from_user.username,
                message.from_user.first_name, message.from_user.last_name,
            )
            config = await get_or_create_shop_config(session)
    await message.answer(config.welcome_text, reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "menu:main")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    async with AsyncSessionLocal() as session:
        config = await get_or_create_shop_config(session)
    await callback.message.edit_text(config.welcome_text, reply_markup=main_menu_keyboard())
    await callback.answer()

@router.message(Command("bind_admin_chat"))
async def bind_admin_chat_handler(message: Message, bot: Bot) -> None:
    if message.chat is None or message.from_user is None:
        return
    if not is_group_chat(message.chat.type):
        return
    if not await is_chat_admin(bot, message.chat.id, message.from_user.id):
        return
    async with AsyncSessionLocal() as session:
        async with session.begin():
            binding = await bind_admin_chat(session, message.chat.id, message.chat.title or "Admin Chat")
    await message.answer("✅ Цю групу успішно прив'язано як адмін-чат. Сюди будуть надходити нові замовлення.")

@router.message(Command("admin"))
async def admin_handler(message: Message, bot: Bot, state: FSMContext) -> None:
    if message.chat.type != "private" or message.from_user is None:
        return
    await state.clear()
    if not await check_admin_rights(message.from_user.id, bot):
        await message.answer("У вас немає доступу до панелі адміністратора.")
        return
    await message.answer("🔧 Панель адміністратора:", reply_markup=admin_main_keyboard())

@router.callback_query(F.data == "admin:main")
async def admin_main_callback(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    await state.clear()
    if not await check_admin_rights(callback.from_user.id, bot):
        return
    await callback.message.edit_text("🔧 Панель адміністратора:", reply_markup=admin_main_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin:products")
async def admin_products_handler(callback: CallbackQuery, bot: Bot) -> None:
    if not await check_admin_rights(callback.from_user.id, bot):
        return
    async with AsyncSessionLocal() as session:
        items = await list_all_products(session)
    if not items:
        await callback.message.edit_text("Товарів ще немає.", reply_markup=admin_main_keyboard())
        return
    text = "📦 Список товарів:\n\n"
    for item in items:
        status = "🟢 Активний" if item.is_active else "🔴 В архіві"
        text += f"ID: {item.id} | {item.title} [{status}]\n"
    await callback.message.edit_text(text, reply_markup=admin_main_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin:add_product")
async def admin_add_product_handler(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if not await check_admin_rights(callback.from_user.id, bot):
        return
    await state.set_state(AdminProductState.waiting_title)
    await callback.message.edit_text("Введіть назву товару:")
    await callback.answer()

@router.message(AdminProductState.waiting_title)
async def admin_product_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text)
    await state.set_state(AdminProductState.waiting_description)
    await message.answer("Введіть опис товару:")

@router.message(AdminProductState.waiting_description)
async def admin_product_desc(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text)
    await state.set_state(AdminProductState.waiting_sizes)
    await message.answer("Введіть розміри та ціни у форматі: S:500, M:500, L:600\n(Або ONE:150 для наліпок та речей без розміру)")

@router.message(AdminProductState.waiting_sizes)
async def admin_product_sizes(message: Message, state: FSMContext) -> None:
    try:
        sizes = parse_sizes_map(message.text)
        await state.update_data(sizes=sizes)
        await state.set_state(AdminProductState.waiting_photo)
        await message.answer("Відправте фото товару:")
    except Exception:
        await message.answer("❌ Невірний формат. Спробуйте ще раз (наприклад: S:500, M:550):")

@router.message(AdminProductState.waiting_photo, F.photo)
async def admin_product_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    async with AsyncSessionLocal() as session:
        async with session.begin():
            product = await create_product(session, title=data['title'], description=data['description'])
            await set_product_photo(session, product, photo_id)
            await replace_sizes(session, product, data['sizes'])
    await state.clear()
    await message.answer(f"✅ Товар '{data['title']}' успішно додано!", reply_markup=admin_main_keyboard())

@router.callback_query(F.data == "admin:set_mono")
async def admin_set_mono_handler(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if not await check_admin_rights(callback.from_user.id, bot):
        return
    await state.set_state(AdminConfigState.waiting_mono_url)
    await callback.message.edit_text("Введіть нове посилання на Банку Monobank:")
    await callback.answer()

@router.message(AdminConfigState.waiting_mono_url)
async def admin_mono_save(message: Message, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            config = await get_or_create_shop_config(session)
            config.mono_jar_url = message.text.strip()
    await state.clear()
    await message.answer("✅ Посилання на банку оновлено!", reply_markup=admin_main_keyboard())

@router.callback_query(F.data == "admin:set_welcome")
async def admin_set_welcome_handler(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if not await check_admin_rights(callback.from_user.id, bot):
        return
    await state.set_state(AdminConfigState.waiting_welcome_text)
    await callback.message.edit_text("Введіть новий текст привітання для користувачів:")
    await callback.answer()

@router.message(AdminConfigState.waiting_welcome_text)
async def admin_welcome_save(message: Message, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            config = await get_or_create_shop_config(session)
            config.welcome_text = message.text.strip()
    await state.clear()
    await message.answer("✅ Текст привітання оновлено!", reply_markup=admin_main_keyboard())

@router.callback_query(F.data == "catalog:view")
async def catalog_handler(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        products = await list_active_products(session)
    if not products:
        await callback.message.edit_text("😔 Зараз немає доступних товарів.", reply_markup=main_menu_keyboard())
        return
    pairs = [(item.id, item.title) for item in products]
    try:
        await callback.message.edit_text("🛒 Оберіть товар з каталогу:", reply_markup=catalog_keyboard(pairs))
    except Exception:
        await callback.message.answer("🛒 Оберіть товар з каталогу:", reply_markup=catalog_keyboard(pairs))
    await callback.answer()

@router.callback_query(F.data.startswith("product:"))
async def product_view_handler(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        product = await get_product(session, product_id)
        sizes = await get_sizes(session, product_id)
    if not product or not product.is_active:
        await callback.answer("Товар наразі недоступний.", show_alert=True)
        return
    text = f"👕 <b>{product.title}</b>\n\n{product.description}\n\n💸 <b>Доступні розміри та ціни:</b>\n"
    text += "\n".join([f"▫️ {s.size} — {Decimal(s.price)} грн" for s in sizes])
    keyboard = sizes_keyboard(product_id, [s.size for s in sizes])
    await callback.message.delete()
    if product.photo_file_id:
        await callback.message.answer_photo(photo=product.photo_file_id, caption=text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("cart:add:"))
async def cart_add_handler(callback: CallbackQuery) -> None:
    _, _, product_id_raw, size = callback.data.split(":")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await ensure_user(
                session, callback.from_user.id, callback.from_user.username,
                callback.from_user.first_name, callback.from_user.last_name,
            )
            try:
                await add_to_cart(session, callback.from_user.id, product_id=int(product_id_raw), size=size, quantity=1)
                await callback.answer("✅ Додано в кошик!", show_alert=False)
            except ValueError:
                await callback.answer("Помилка додавання.", show_alert=True)

@router.callback_query(F.data == "cart:view")
async def cart_view_callback(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        rows = await list_cart(session, callback.from_user.id)
    if not rows:
        try:
            await callback.message.edit_text("Ваш кошик порожній 😔", reply_markup=main_menu_keyboard())
        except Exception:
            await callback.message.answer("Ваш кошик порожній 😔", reply_markup=main_menu_keyboard())
        return
    total = Decimal("0")
    text = "🛒 <b>Ваш кошик:</b>\n\n"
    for item, product in rows:
        line_total = Decimal(str(item.price)) * item.quantity
        total += line_total
        text += f"▫️ {product.title} (Розмір: {item.size})\n   {item.quantity} шт x {Decimal(item.price)} грн = {line_total} грн\n"
    text += f"\n💰 <b>Разом до сплати: {total} грн</b>"
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text, reply_markup=cart_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "cart:clear")
async def cart_clear_callback(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await clear_cart(session, callback.from_user.id)
    await callback.answer("Кошик очищено!")
    await callback.message.edit_text("Ваш кошик порожній 😔", reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "checkout:start")
async def checkout_start_handler(callback: CallbackQuery, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        rows = await list_cart(session, callback.from_user.id)
    if not rows:
        await callback.answer("Кошик порожній", show_alert=True)
        return
    await state.set_state(CheckoutState.waiting_contact)
    await callback.message.answer("📝 Введіть ваше <b>Прізвище, Ім'я та номер телефону</b>:", parse_mode="HTML")
    await callback.answer()

@router.message(CheckoutState.waiting_contact)
async def checkout_contact_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(contact=message.text)
    await state.set_state(CheckoutState.waiting_delivery)
    await message.answer("🚚 Введіть <b>дані для доставки</b> (Місто, номер відділення Нової Пошти):", parse_mode="HTML")

@router.message(CheckoutState.waiting_delivery)
async def checkout_delivery_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(delivery=message.text)
    async with AsyncSessionLocal() as session:
        rows = await list_cart(session, message.from_user.id)
        config = await get_or_create_shop_config(session)
    total = sum([Decimal(str(item.price)) * item.quantity for item, _ in rows])
    await state.update_data(total=str(total))
    
    payment_text = (
        f"💳 <b>Оплата замовлення</b>\n\n"
        f"Сума до сплати: <b>{total} грн</b>\n\n"
        f"Перейдіть за посиланням та оплатіть замовлення:\n👉 {config.mono_jar_url}\n\n"
        f"📸 <b>Після оплати, будь ласка, надішліть сюди скріншот квитанції.</b>"
    )
    await state.set_state(CheckoutState.waiting_receipt)
    await message.answer(payment_text, parse_mode="HTML", disable_web_page_preview=True)

@router.message(CheckoutState.waiting_receipt, F.photo)
async def checkout_receipt_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            config = await get_or_create_shop_config(session)
            order = await create_order_from_cart(
                session,
                telegram_id=message.from_user.id,
                phone=data.get("contact", ""),
                address=data.get("delivery", ""),
                receipt_photo_id=photo_id,
                currency=config.currency,
            )
            binding = await get_active_admin_binding(session)
            await session.refresh(order)
            await session.refresh(order, attribute_names=["items"])

    await state.clear()
    await message.answer(
        f"✅ <b>Дякуємо! Ваше замовлення #{order.id} прийнято.</b>\n"
        f"Ми перевіримо оплату та повідомимо вас про зміну статусу.", 
        parse_mode="HTML", reply_markup=main_menu_keyboard()
    )

    if binding is not None:
        lines = [
            f"🔔 <b>Нове замовлення #{order.id}</b>",
            f"👤 Клієнт: @{message.from_user.username or 'Без юзернейму'} ({message.from_user.id})",
            f"📞 Контакти: {data.get('contact', '')}",
            f"🚚 Доставка: {data.get('delivery', '')}",
            f"💰 Сума: {Decimal(order.total_amount)} {order.currency}",
            "\n📦 <b>Позиції:</b>"
        ]
        for item in order.items:
            lines.append(f"▫️ {item.title} | {item.size} | {item.quantity} шт x {Decimal(item.unit_price)} грн")
        
        try:
            sent = await bot.send_photo(
                binding.chat_id, 
                photo=photo_id, 
                caption="\n".join(lines), 
                reply_markup=order_status_keyboard(order.id),
                parse_mode="HTML"
            )
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    db_order = await get_order(session, order.id)
                    if db_order:
                        await set_order_admin_message(session, db_order, sent.message_id)
        except Exception:
            pass

@router.callback_query(F.data.startswith("ostatus:"))
async def order_status_handler(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        return
    _, order_id_raw, status_raw = parts
    order_id = int(order_id_raw)
    
    try:
        status = OrderStatus(status_raw)
    except ValueError:
        return

    async with AsyncSessionLocal() as session:
        async with session.begin():
            order = await get_order(session, order_id)
            if not order:
                await callback.answer("Замовлення не знайдено", show_alert=True)
                return
            if order.status == status:
                await callback.answer("Цей статус вже встановлено", show_alert=False)
                return
            await set_order_status(session, order, status)
            user_id = order.telegram_id

    status_translations = {
        OrderStatus.in_process: "🔄 Взято в роботу",
        OrderStatus.completed: "✅ Виконано та відправлено",
        OrderStatus.cancelled: "❌ Скасовано"
    }
    
    try:
        current_text = callback.message.caption or callback.message.text or ""
        lines = current_text.split('\n')
        if lines and lines[0].startswith("🔔"):
            lines[0] = f"🔔 Замовлення #{order_id} [{status_translations[status]}]"
        
        if callback.message.photo:
            await callback.message.edit_caption(
                caption="\n".join(lines), 
                reply_markup=order_status_keyboard(order_id),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                text="\n".join(lines), 
                reply_markup=order_status_keyboard(order_id),
                parse_mode="HTML"
            )
    except Exception:
        pass

    await callback.answer(f"Статус змінено на: {status.value}")
    
    try:
        await bot.send_message(
            user_id, 
            f"🔔 Статус вашого замовлення <b>#{order_id}</b> змінено!\nНовий статус: <b>{status_translations[status]}</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass

def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp