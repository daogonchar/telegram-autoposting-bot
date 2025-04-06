import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import F
from aiogram.types import Message
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv
import aiohttp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)

session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(F.text == "/start")
async def start_handler(message: types.Message):
    await message.answer("Привет! Я на вебхуках и работаю исправно 😉\nЗапиши мне голосовое — я расшифрую и помогу превратить его в пост")

@dp.message(F.voice)
async def voice_handler(message: Message, bot: Bot):
    file_info = await bot.get_file(message.voice.file_id)
    file_path = file_info.file_path
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

    await message.answer("Получил голосовое. Начинаю расшифровку...")

    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as response:
            audio_data = await response.read()

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = aiohttp.FormData()
    data.add_field('file', audio_data, filename="audio.ogg", content_type='audio/ogg')
    data.add_field('model', 'whisper-1')

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, data=data) as resp:
            result = await resp.json()
            text = result.get("text")

    if text:
        await message.answer(f"Расшифровка:\n{text}")
    else:
        await message.answer("Не удалось расшифровать голосовое сообщение 😔")

if __name__ == '__main__':
    import asyncio
    from aiogram.webhook.aiohttp_server import setup_application
    from aiohttp import web

    async def on_startup(app):
        webhook_url = os.getenv("RENDER_EXTERNAL_URL") + "/webhook"
        await bot.set_webhook(webhook_url)
        print(f"Webhook установлен: {webhook_url}")

    async def on_shutdown(app):
        await bot.session.close()

    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    dp.include_routers(dp)  # Подключаем маршруты
    setup_application(app, dp, path="/webhook")
    web.run_app(app, port=int(os.getenv("PORT", 8080)))
