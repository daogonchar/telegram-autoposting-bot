import os
import logging
import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.webhook.security import IPFilter
from aiohttp import web
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
openai_client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)

@dp.message(F.voice)
async def handle_voice(message: Message):
    file_id = message.voice.file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    voice_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

    async with aiohttp.ClientSession() as session:
        async with session.get(voice_url) as response:
            if response.status == 200:
                audio_data = await response.read()

                with open("temp.ogg", "wb") as f:
                    f.write(audio_data)

                with open("temp.ogg", "rb") as f:
                    transcript = openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        response_format="text"
                    )

                await message.answer(f"Расшифровка:
<pre>{transcript}</pre>", parse_mode=ParseMode.HTML)
            else:
                await message.answer("Не удалось скачать голосовое сообщение.")

@dp.message(F.text == "/start")
async def handle_start(message: Message):
    await message.answer("Привет! Я на вебхуках и теперь умею расшифровывать голосовые сообщения ✨")


async def on_startup(bot: Bot) -> None:
    webhook_url = os.getenv("RENDER_EXTERNAL_URL") + "/webhook/" + WEBHOOK_SECRET
    await bot.set_webhook(webhook_url)


async def main() -> web.Application:
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path="/webhook/" + WEBHOOK_SECRET)
    setup_application(app, dp, bot=bot)
    await on_startup(bot)
    return app

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
