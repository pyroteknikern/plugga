from app.create_bot import create_bot
from app.reddit import scrape
from app.cogs.loops import create_members
from app.constants import token
import logging
import asyncio
import os


bot = create_bot()


@bot.event
async def on_ready():
    logging.info("Starting bot")
    scrape("memes")
    await create_members(bot)


async def load():
    for filename in os.listdir("./app/cogs"):
        if filename.endswith(".py"):
 #           await bot.load_extension(f"app.cogs.{filename[:-3]}")

            await bot.load_extension("app.cogs.loops")

async def main():
    await load()
    await bot.start(token)

asyncio.run(main())

