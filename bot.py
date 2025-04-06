from aiogram import Bot, Dispatcher, executor, types
import os

bot = Bot(token=os.getenv("API_TOKEN"))
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Привет! Я готов к автопостингу 🧘‍♂️")

if __name__ == '__main__':
    executor.start_polling(dp)
