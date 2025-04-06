import logging
import os
import tempfile
import asyncio

from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
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
CHANNEL_ID = os.getenv("CHANNEL_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я на вебхуках и жду вашу голосовую заметку 🎙")

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
            user_text = transcript['text']

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}]
        )
        bot_reply = response.choices[0].message['content']

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Опубликовать в канал", callback_data=f"post_to_channel:{bot_reply}")]
        ])

        await message.answer(f"📝 Расшифровка: <i>{user_text}</i>\n\n🤖 Ответ: {bot_reply}", reply_markup=keyboard)
    elif message.text:
        await message.answer("Пожалуйста, пришлите голосовое сообщение 🎙")

@router.callback_query()
async def handle_callback(callback_query: types.CallbackQuery, bot: Bot):
    data = callback_query.data
    if data.startswith("post_to_channel:"):
        bot_reply = data[len("post_to_channel:"):]
        await bot.send_message(chat_id=CHANNEL_ID, text=bot_reply)
        await callback_query.answer("✅ Сообщение опубликовано в канале.")

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
    asyncio.run(web._run_app(main(), port=int(os.getenv("PORT"))))
