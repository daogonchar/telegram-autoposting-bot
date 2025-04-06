from aiogram import Router, F
from aiogram.types import Message
from openai import AsyncOpenAI
import aiohttp
import tempfile
import os

router = Router()
openai_client = AsyncOpenAI()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Привет! Я на вебхуках и жду вашу голосовую заметку 🎙")

@router.message(F.voice)
async def handle_voice(message: Message, bot):
    voice = message.voice
    file_info = await bot.get_file(voice.file_id)
    file_path = file_info.file_path
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"

    # Загружаем голосовое сообщение во временный файл
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
                    tmp_file.write(await resp.read())
                    tmp_file_path = tmp_file.name

    # Расшифровываем через OpenAI Whisper
    with open(tmp_file_path, "rb") as audio_file:
        transcript = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    os.remove(tmp_file_path)  # Чистим временный файл

    await message.answer(f"📝 Расшифровка: {transcript.text}")
