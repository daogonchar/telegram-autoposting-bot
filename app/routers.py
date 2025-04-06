# app/routers.py

import os
import tempfile
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ContentType
from openai import Audio
from pydub import AudioSegment

router = Router()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@router.message(F.text)
async def handle_text(message: Message):
    await message.answer(f"Вы отправили текст: {message.text}")

@router.message(F.voice)
async def handle_voice(message: Message, bot):
    try:
        # Получение файла
        file_info = await bot.get_file(message.voice.file_id)
        file_path = file_info.file_path

        # Скачивание файла
        with tempfile.NamedTemporaryFile(delete=False, suffix=".oga") as tmp_oga:
            await bot.download_file(file_path, destination=tmp_oga)
            oga_path = tmp_oga.name

        # Конвертация в mp3
        mp3_path = oga_path.replace(".oga", ".mp3")
        AudioSegment.from_file(oga_path).export(mp3_path, format="mp3")

        # Отправка в OpenAI (через старый API < 1.0)
        with open(mp3_path, "rb") as audio_file:
            transcript = Audio.transcribe("whisper-1", audio_file, api_key=OPENAI_API_KEY)

        await message.answer(f"Расшифровка: {transcript['text']}")

        # Очистка временных файлов
        os.remove(oga_path)
        os.remove(mp3_path)

    except Exception as e:
        logging.exception("Ошибка при обработке голосового сообщения")
        await message.answer("Произошла ошибка при обработке голосового сообщения.")
