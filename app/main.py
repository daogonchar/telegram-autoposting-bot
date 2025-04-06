# app/main.py
import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import TokenBasedRequestHandler
from aiogram.client.default import DefaultBotProperties
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import router

# Загружаем .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_PATH = f"/{WEBHOOK_SECRET}"
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") + WEBHOOK_PATH
PORT = int(os.getenv("PORT", 10000))

# Настройка бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

# FastAPI
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Установка вебхука при старте
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

# Обработка входящих вебхуков
app.router.add_route(
    path=WEBHOOK_PATH,
    route=TokenBasedRequestHandler(dispatcher=dp, bot=bot),
    methods=["POST"]
)

# Запуск (если локально)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT)

