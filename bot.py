import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(message: types.Message):
    await message.answer("Привет! Я на вебхуках и работаю исправно 😉")

async def on_startup(app):
    webhook_url = f"{os.getenv('RENDER_EXTERNAL_URL')}{WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url)
    print(f"Webhook установлен на {webhook_url}")

async def on_shutdown(app):
    await bot.delete_webhook()

app = web.Application()
app["bot"] = bot

SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)

app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    setup_application(app, dp, bot=bot)
    web.run_app(app, port=PORT)
