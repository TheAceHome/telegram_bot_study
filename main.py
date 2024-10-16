import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor


logging.basicConfig(level=logging.INFO)

API_TOKEN = '7922381649:AAFRc4QuL1vin8baSj0k1TS5L097ejZr6yE'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я ваш Телеграмм бот.")

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.reply("Напишите /start, чтобы начать.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)