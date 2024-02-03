import discord
from discord.ext import commands
from app.constants import token

import logging

logging.basicConfig(filename="plugga_bot.log", level=logging.INFO)


class Bot(commands.Bot):
    def __init__(self):
        logging.info("starting")
        super().__init__(
                command_prefix='!',
                intents=discord.Intents.all()
                )

    async def setup_hook(self):
        await self.load_extension("cogs.loops")
        await self.load_extension("cogs.user_commands")


Bot().run(token)
