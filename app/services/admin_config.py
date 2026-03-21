from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import AdminChatBinding, ShopConfig


async def get_or_create_shop_config(session: AsyncSession) -> ShopConfig:
    result = await session.execute(select(ShopConfig).where(ShopConfig.id == 1))
    config = result.scalar_one_or_none()
    if config is None:
        config = ShopConfig(id=1, currency=settings.admin_default_currency)
        session.add(config)
        await session.flush()
    return config


async def get_active_admin_binding(session: AsyncSession) -> AdminChatBinding | None:
    result = await session.execute(select(AdminChatBinding).where(AdminChatBinding.is_active.is_(True)))
    return result.scalar_one_or_none()


async def bind_admin_chat(session: AsyncSession, chat_id: int, title: str) -> AdminChatBinding:
    current = await get_active_admin_binding(session)
    if current and current.chat_id != chat_id:
        current.is_active = False

    result = await session.execute(select(AdminChatBinding).where(AdminChatBinding.chat_id == chat_id))
    binding = result.scalar_one_or_none()
    if binding is None:
        binding = AdminChatBinding(chat_id=chat_id, title=title, is_active=True)
        session.add(binding)
    else:
        binding.is_active = True
        binding.title = title
    await session.flush()
    return binding
