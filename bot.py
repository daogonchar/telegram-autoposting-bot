import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram import Router
from dotenv import load_dotenv
import asyncio

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота из переменной окружения
API_TOKEN = os.getenv("API_TOKEN")

# Настройка бота и диспетчера
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Роутер
router = Router()

@router.message(commands=["start"])
async def start_handler(message: Message):
    await message.answer("Привет! Бот работает, готов к автопостингу ✨")

dp.include_router(router)

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
