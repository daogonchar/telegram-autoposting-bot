import logging
import os
import tempfile
import asyncio

from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.filters import Command
from aiohttp import web
from dotenv import load_dotenv
import openai
import aiohttp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") + "/" + WEBHOOK_SECRET
openai.api_key = os.getenv("OPENAI_API_KEY")

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я на вебхуках и работаю исправно 😉")

@router.message()
async def handle_voice_or_text(message: Message, bot: Bot):
    if message.voice:
        file_info = await bot.get_file(message.voice.file_id)
        file_path = file_info.file_path
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
                    tmp_file.write(await response.read())
                    tmp_file_path = tmp_file.name

        with open(tmp_file_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            await message.answer(f"Расшифровка: {transcript['text']}")

    elif message.text:
        await message.answer(f"Вы написали: {message.text}")

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/" + WEBHOOK_SECRET)
    setup_application(app, dp, bot=bot)

    await bot.set_webhook(WEBHOOK_URL)
    return app

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = asyncio.run(main())
    web.run_app(app, port=int(os.getenv("PORT")))
