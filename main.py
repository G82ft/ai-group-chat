import asyncio

from aiogram import Dispatcher, Bot

from commands import cmd
import config
from generation import gen

dp = Dispatcher()
dp.include_router(gen)
dp.include_router(cmd)
bot = Bot(token=config.get("tg_token"))


async def main():
    await dp.start_polling(bot)


asyncio.run(main())
