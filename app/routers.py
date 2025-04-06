import os
import tempfile
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ContentType
from openai import AsyncOpenAI
from httpx import AsyncClient
from pydub import AudioSegment

router = Router()

# Инициализация OpenAI клиента (новая версия SDK)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
http_client = AsyncClient()
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, http_client=http_client)


@router.message(F.text)
async def handle_text(message: Message):
    await message.answer(f"Вы отправили текст: {message.text}")


@router.message(F.voice)
async def handle_voice(message: Message, bot):
    try:
        # Получение информации о файле
        file_info = await bot.get_file(message.voice.file_id)
        file_path = file_info.file_path

        # Скачивание файла во временное хранилище
        with tempfile.NamedTemporaryFile(delete=False, suffix=".oga") as tmp_oga:
            await bot.download_file(file_path, destination=tmp_oga)
            oga_path = tmp_oga.name

        # Конвертация .oga в .mp3
        mp3_path = oga_path.replace(".oga", ".mp3")
        AudioSegment.from_file(oga_path).export(mp3_path, format="mp3")

        # Расшифровка через OpenAI Whisper
        with open(mp3_path, "rb") as audio_file:
            transcript = await openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        # Отправка результата пользователю
        await message.answer(f"Расшифровка: {transcript.text}")

        # Удаление временных файлов
        os.remove(oga_path)
        os.remove(mp3_path)

    except Exception as e:
        logging.exception("Ошибка при обработке голосового сообщения")
        await message.answer("Произошла ошибка при обработке голосового сообщения.")
