# app/main.py

import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
import uvicorn

from app.routers import router  # Только импорт router

# Загрузка переменных окружения
load_dotenv()

# Переменные из .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_PATH = f"/{WEBHOOK_SECRET}"
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") + WEBHOOK_PATH
PORT = int(os.getenv("PORT", 10000))

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)  # Подключаем router один раз

# Инициализация FastAPI
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

@app.post(WEBHOOK_PATH)
async def handle_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data)  # ← Преобразуем dict в объект Update
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT)
