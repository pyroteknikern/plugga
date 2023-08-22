import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from datetime import datetime, date

load_dotenv()
token = os.getenv('discordToken')
print(token)
VOICE_CHANNEL = 1137055625973608538
print(VOICE_CHANNEL)
GUILD_ID = 1137055625042481213
TEXT_CHANNEL = 1143592135111741450
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


async def get_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()


@bot.command(name="test")
async def test(ctx):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    db = SessionLocal()
    users = (await db.execute(select(User))).scalars().all()
    for j, i in enumerate(users):
        print(i.username)
    await db.close()


def get_index(member: str, members: list):
    for i, mem in enumerate(members):
        if mem.username == member:
            return i


@tasks.loop(minutes=1)
async def check_time():
    if int(datetime.now().strftime("%H")) < 5:
        return

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    db = SessionLocal()
    db_members = (await db.execute(select(User))).scalars().all()

    channel = bot.get_channel(VOICE_CHANNEL)
    vc_members = channel.members
    for vc_member in vc_members:
        index = get_index(vc_member.name, db_members)
        db_members[index].day_time += 1
        db_members[index].week_time += 1
        db_members[index].total_time += 1
    await db.commit()
    await db.close()


async def get_user(user: str, db):
    db_members = (await db.execute(select(User))).scalars().all()
    for db_user in db_members:
        if db_user.username == user:
            return db_user


@bot.event
async def create_members():
    guild = bot.get_guild(GUILD_ID)
    memberList = guild.members

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    db = SessionLocal()

    for i, member in enumerate(memberList):
        if member.bot:
            continue
        if await get_user(member.name, db) is None:
            try:
                new_user = User(username=member.name,
                                total_time=0,
                                week_time=0,
                                day_time=0,
                                missed_days=0)
                db.add(new_user)
                await db.commit()
            except:
                pass
            continue

    await db.close()


@bot.command(name="mytime")
async def display_stat(ctx):
    await send_stat([ctx.author], ctx)


async def send_stat(members, ctx=None):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    db = SessionLocal()
    message = ""
    for member in members:
        user = await get_user(member.name, db)
        channel = bot.get_channel(TEXT_CHANNEL)
        try:
            message += f"{member.mention}\nTotal: {format(user.total_time)}\nToday: {format(user.day_time)}\nThis week: {format(user.week_time)}\nFails: {user.missed_days}\nSkuld: {user.missed_days*50}"
        except:
            pass
    if ctx is not None:
        await ctx.send(message)
    else:
        await channel.purge(limit=2)
        await channel.send(message)
    await db.close()


def format(minutes):
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min"


@tasks.loop(minutes=60)
async def time_reset():
    guild = bot.get_guild(GUILD_ID)
    memberList = guild.members

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    db = SessionLocal()
    db_members = (await db.execute(select(User))).scalars().all()
    today = date.today().weekday()
    if int(datetime.now().strftime("%H")) == 0:
        for member in db_members:
            if member.day_time < 90 and today < 5:
                member.missed_days += 1
            member.day_time = 0
        if today == 0:
            await send_stat(memberList)
            await create_members()
            for member in db_members:
                if member.week_time < 450:
                    member.missed_days += 1
                member.week_time = 0
    await db.commit()
    await db.close()


@bot.event
async def on_ready():
    check_time.start()
    time_reset.start()
    await create_members()

bot.run(token)
