from discord.ext import commands
import discord


def create_bot():
    bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
    return bot
