import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, date
import pytz

SWE_TIME = pytz.timezone("Europe/Stockholm")

load_dotenv()

token = os.getenv('discordToken')
VOICE_CHANNEL = int(os.getenv('voiceChannel'))
GUILD_ID = int(os.getenv('guildId'))
TEXT_CHANNEL = int(os.getenv('textChannel'))

print(VOICE_CHANNEL)
print(GUILD_ID)
print(TEXT_CHANNEL)

day_reset_time = 0
week_reset_day = 0
intents = discord.Intents(messages=True,
                          guilds=True,
                          members=True,
                          message_content=True,
                          presences=True)
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())


engine = create_async_engine("sqlite+aiosqlite:///db.sqlite3",
                             connect_args={"check_same_thread": False})
SessionLocal = async_sessionmaker(engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    total_time: Mapped[int]
    week_time: Mapped[int]
    day_time: Mapped[int]
    missed_days: Mapped[int]


async def gen_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    db = SessionLocal()
    return db


@bot.command(name="test")
async def test(ctx):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    db = SessionLocal()
    users = (await db.execute(select(User))).scalars().all()
    for j, i in enumerate(users):
        print(i.username)
    await db.close()


@bot.command(name="test2")
async def test2(ctx):
    db = await gen_db()
    users = (await db.execute(select(User))).scalars().all()
    for j, i in enumerate(users):
        print(i.username)
    await db.close()


async def get_user_by_username(user: str, db):
    db_members = (await db.execute(select(User))).scalars().all()
    for db_user in db_members:
        if db_user.username == user:
            return db_user


@bot.event
async def create_members():
    guild = bot.get_guild(GUILD_ID)
    memberList = guild.members
    db = await gen_db()
    for i, member in enumerate(memberList):
        if member.bot:
            continue
        if await get_user_by_username(member.name, db) is None:
            new_user = User(username=member.name,
                            total_time=0,
                            week_time=0,
                            day_time=0,
                            missed_days=0)
            db.add(new_user)
            await db.commit()
    await db.close()


@bot.command(name="mytime")
async def display_stat(ctx):
    await send_stat([ctx.author], ctx)


async def send_stat(server_members, ctx=None):
    db = await gen_db()
    message = ""
    channel = bot.get_channel(TEXT_CHANNEL)
    for server_member in server_members:
        if server_member.bot:
            continue
        db_member = await get_user_by_username(server_member.name, db)
        message += f"{server_member.mention}\n"
        if db_member is None:
            message += "your name is not registerd\n"
            continue
        if ctx is not None:
            message += f"Today: {format(db_member.day_time)}\n"
        message += f"Total: {format(db_member.total_time)}\n"
        message += f"This week: {format(db_member.week_time)}\n"
        message += f"Fails: {db_member.missed_days}\n"
        message += f"Skuld: {db_member.missed_days*50}\n"
    await db.close()
    if ctx is not None:
        await ctx.send(message)
    else:
        await channel.purge(limit=2)
        await channel.send(message)


def format(minutes):
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min"


def get_current_hour() -> int:
    return int(datetime.now(SWE_TIME).strftime("%H"))


@tasks.loop(minutes=60)
async def time_reset():
    guild = bot.get_guild(GUILD_ID)
    server_members = guild.members
    db = await gen_db()
    db_members = (await db.execute(select(User))).scalars().all()
    today = date.today().weekday()
    if get_current_hour() == day_reset_time:
        for db_member in db_members:
            if db_member.day_time < 90 and today < 5:
                db_member.missed_days += 1
            db_member.day_time = 0
        if today == week_reset_day:
            await send_stat(server_members)
            await create_members()
            for db_member in db_members:
                if db_member.week_time < 450:
                    db_member.missed_days += 1
                db_member.week_time = 0
    await db.commit()
    await db.close()


@tasks.loop(minutes=1)
async def check_time():
    if get_current_hour() < 5:
        return
    db = await gen_db()
    channel = bot.get_channel(VOICE_CHANNEL)
    vc_members = channel.members
    for vc_member in vc_members:
        db_user = await get_user_by_username(vc_member.name, db)
        if db_user is None:
            continue
        db_user.day_time += 1
        db_user.week_time += 1
        db_user.total_time += 1
    await db.commit()
    await db.close()


@bot.event
async def on_ready():
    check_time.start()
    time_reset.start()
    await create_members()

bot.run(token)
