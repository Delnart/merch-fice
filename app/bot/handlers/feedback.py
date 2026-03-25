from aiogram import Router, F
from aiogram.types import Message, ReactionTypeEmoji
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.states import FeedbackState
from app.db.models import AdminChatBinding
from app.services.admin_config import get_active_admin_binding

router = Router()

@router.message(F.text.startswith("/support"))
async def support_start(message: Message, state: FSMContext):
    await state.set_state(FeedbackState.waiting_message)
    await message.answer("Напишіть ваше повідомлення для адміністраторів:")

@router.message(FeedbackState.waiting_message)
async def process_feedback(message: Message, state: FSMContext, session: AsyncSession):
    admin_binding = await get_active_admin_binding(session)
    if not admin_binding:
        await message.answer("Помилка: чат адміністраторів не налаштований.")
        return

    text = f"#T{message.from_user.id}\nПовідомлення від @{message.from_user.username}:\n{message.text}"
    await message.bot.send_message(admin_binding.chat_id, text)
    await message.answer("Ваше повідомлення надіслано!")
    await state.clear()

@router.message(F.reply_to_message & F.chat.type.in_(['group', 'supergroup']))
async def admin_reply(message: Message):
    if message.reply_to_message.text and message.reply_to_message.text.startswith("#T"):
        user_id_str = message.reply_to_message.text.split("\n")[0].replace("#T", "")
        try:
            user_id = int(user_id_str)
            await message.bot.send_message(user_id, f"Відповідь від адміністратора:\n{message.text}")
            await message.react([ReactionTypeEmoji(emoji="👍")])
        except ValueError:
            pass