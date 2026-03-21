from contextlib import asynccontextmanager

from aiogram import Bot
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.bot.router import build_dispatcher
from app.config import settings
from app.db.init_db import init_db


bot = Bot(token=settings.bot_token)
dp = build_dispatcher()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/setup/webhook")
async def setup_webhook() -> dict[str, bool]:
    await bot.set_webhook(
        url=f"{settings.app_base_url}/webhook/telegram",
        secret_token=settings.webhook_secret,
        allowed_updates=["message", "callback_query"],
    )
    return {"ok": True}


@app.get("/setup/delete_webhook")
async def delete_webhook() -> dict[str, bool]:
    await bot.delete_webhook(drop_pending_updates=False)
    return {"ok": True}


@app.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if x_telegram_bot_api_secret_token != settings.webhook_secret:
        raise HTTPException(status_code=401, detail="unauthorized")
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)
    return JSONResponse({"ok": True})
