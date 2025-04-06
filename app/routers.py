# app/routers.py

import os
import tempfile
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ContentType
from aiogram import Bot
from openai import AsyncOpenAI
from pydub import AudioSegment

# Инициализация роутера
router = Router()

# Инициализация OpenAI клиента
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Обработка текстовых сообщений
@router.message(F.text)
async def handle_text(message: Message):
    await message.answer(f"Вы отправили текст: {message.text}")

# Обработка голосовых сообщений
@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot):
    try:
        file = await bot.get_file(message.voice.file_id)
        file_path = file.file_path

        # Скачиваем .oga во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".oga") as tmp_oga:
            await bot.download_file(file_path, destination=tmp_oga)
            oga_path = tmp_oga.name

        # Конвертируем в mp3
        mp3_path = oga_path.replace(".oga", ".mp3")
        AudioSegment.from_file(oga_path).export(mp3_path, format="mp3")

        # Распознаем голос через Whisper (OpenAI)
        with open(mp3_path, "rb") as audio_file:
            transcription = await openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        await message.answer(f"Расшифровка: {transcription.text}")

        # Удаляем временные файлы
        os.remove(oga_path)
        os.remove(mp3_path)

    except Exception as e:
        logging.exception("Ошибка при расшифровке голосового сообщения")
        await message.answer("Произошла ошибка при обработке голосового сообщения.")
