import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram import Router
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
import openai
import tempfile
import aiohttp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") + "/" + WEBHOOK_SECRET
openai.api_key = os.getenv("OPENAI_API_KEY")

router = Router()

@router.message(commands=["start"])
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

        audio_file = open(tmp_file_path, "rb")
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
    web.run_app(main())
