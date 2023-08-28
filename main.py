import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker)
from datetime import datetime, date, timedelta
import pytz

from models import Base, User, Date

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
format = "%d-%m-%Y"
intents = discord.Intents(messages=True,
                          guilds=True,
                          members=True,
                          message_content=True,
                          presences=True)
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())


engine = create_async_engine("sqlite+aiosqlite:///db.sqlite3",
                             connect_args={"check_same_thread": False})
SessionLocal = async_sessionmaker(engine)


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


@bot.command(name="accept-challange")
async def accept_challange(ctx):
    db = await gen_db()
    date_period = get_date_by_period(db)
    
    db_member = await get_user_by_username(ctx.author.name, db)
    if db_member.period_failed != 0:
        await db.close()
        await ctx.send('Error: 69, lol get blocked')
        return
    db_member.challange_accepted = True
    await ctx.send('Sucefully joined the chllange, best of luck!')
    await db.commit()
    await db.close()


@bot.command(name="quit-challange")
async def quit_challange(ctx):
    db = await gen_db()
    cp = await current_period(db)
    db_periods = (await db.execute(select(Date))).scalars().all()
    db_member = await get_user_by_username(ctx.author.name, db)
    if not cp and db_member.period_failed != 0:
        await db.close()
        await ctx.send("there is not currently an active period")
        return
    db_member.challange_accepted = False
    db_member.period_failed = 2
    await ctx.send("I KNEW IT! \n jk, this is pre-written - still sad that u quit")
    await db.commit()
    await db.close()


async def current_period(db):
    db_periods = (await db.execute(select(Date))).scalars().all()
    today = datetime.today().strftime(format)
    today = datetime.strptime(today, format)
    for db_period in db_periods:
        db_end = datetime.strptime(db_period.end_date, format)
        db_start = datetime.strptime(db_period.start_date, format)
        if today >= db_start and today < db_end:
            return db_period.period
    return False

async def get_date_by_period(db, period):
    db_periods = (await db.execute(select(Date))).scalars().all()
    for db_period in db_periods:
        if db_period.period == period:
            return db_period

@bot.command(name="mytime")
async def display_stat(ctx):
    await send_stat([ctx.author], ctx)


@bot.command(name="period")
async def set_test_date(ctx, date):
    if ctx.channel.id != int(os.getenv("modChannel")):
        return
    a = date.split("-")
    start_date_list = a[0].split(",")
    end_date_list = a[1].split(",")
    period = int(a[2])
    start_date = f"{str(start_date_list[0])}-"
    start_date += f"{str(start_date_list[1])}-"
    start_date += f"{str(start_date_list[2])}"

    end_date = f"{str(end_date_list[0])}-"
    end_date += f"{str(end_date_list[1])}-"
    end_date += f"{str(end_date_list[2])}"

    format = "%d-%m-%Y"
    res = True

    try:
        res = bool(datetime.strptime(start_date, format))
    except ValueError:
        res = False
    if not res:
        await ctx.send("this is not the correct format")
        return
    today = datetime.today().strftime(format)
    today = datetime.strptime(today, format)
    if today > datetime.strptime(start_date,
                                 format) or datetime.strptime(start_date,
                                                              format) >= datetime.strptime(end_date,
                                                                                           format):
        await ctx.send("this is not a valid period")
        return

    db = await gen_db()
    if await date_overlaps(start_date, end_date, db, ctx, format):
        await db.close()
        return
    new_start_date = Date(start_date=start_date, end_date=end_date, period=period)
    db.add(new_start_date)
    await db.commit()
    await db.close()
    await ctx.send("period was added")

async def reset_user(db, username):
    db_member = await get_user_by_username(username, db)
    db_member.total_time = 0
    db_member.week_time = 0
    db_member.day_time = 0
    db_member.missed_days = 0
    db_member.challange_accepted = False


async def delete_prev_period_data(db):
    db_dates = (await db.execute(select(Date))).scalars().all()
    db_members = (await db.execute(select(User))).scalars().all()
    for db_user in db_members:
        reset_user(db, db_user.name)
    await db.delete(db_dates[0])
    await db.commit()
    await db.close()

async def date_overlaps(start_date, end_date, db, ctx, format):
    db_dates = (await db.execute(select(Date))).scalars().all()
    start_date = datetime.strptime(start_date, format)
    end_date = datetime.strptime(end_date, format)
    for i, db_period in enumerate(db_dates):
        db_end = datetime.strptime(db_period.end_date, format)
        db_start = datetime.strptime(db_period.start_date, format)
        if start_date <= db_end and start_date >= db_start:
            await ctx.send(f"{start_date} cannot be within period: {db_period.period}")
            return True
        if end_date <= db_end and end_date >= db_start:
            await ctx.send(f"{end_date} cannot be within period: {db_period.period}")
            return True
        if end_date >= db_end and start_date <= db_start:
            await ctx.send(f"bloced by period: {db_period.period}")
            return True
    return False


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
                            missed_days=0,
                            challange_accepted=False,
                            period_failed=0)
            db.add(new_user)
            await db.commit()
    await db.close()


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
            message += f"Today: {format_time(db_member.day_time)}\n"
        message += f"This week: {format_time(db_member.week_time)}\n"
        message += f"Total: {format_time(db_member.total_time)}\n"
        message += f"Missed days: {db_member.missed_days}\n"
        message += f"Dept: {db_member.missed_days*50}\n"
    await db.close()
    if ctx is not None:
        await ctx.send(message)
    else:
        await channel.purge(limit=2)
        await channel.send(message)


def format_time(minutes):
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min"


def get_current_hour() -> int:
    return int(datetime.now(SWE_TIME).strftime("%H"))


async def count_missed_days(db) -> bool:
    db_periods = (await db.execute(select(Date))).scalars().all()
    today = datetime.today().strftime(format)
    today = datetime.strptime(today, format)
    for db_period in db_periods:
        db_end = datetime.strptime(db_period.end_date, format)
        db_start = datetime.strptime(db_period.start_date, format)
        stop_date = db_end - timedelta(days=14)
        if today >= db_start and today < stop_date:
            return True
    return False


@tasks.loop(minutes=60)
async def time_reset():
    guild = bot.get_guild(GUILD_ID)
    server_members = guild.members
    db = await gen_db()
    db_members = (await db.execute(select(User))).scalars().all()
    today_num = date.today().weekday()
    today = datetime.today().strftime(format)
    today = datetime.strptime(today, format)
    

    if get_current_hour() == day_reset_time:
        cp = current_period(db)
        cp_period = await get_date_by_period(db, cp)
        if cp_period is not None:
            cp_period_end = datetime.strptime(cp_period.end_date, format)
            if cp_period_end == today:
                for db_member in db_members:
                    if db_member.period_failed != 0:
                        db_member.period_failed -= 1
                delete_prev_period_data(db)
        for db_member in db_members:
            count_days = await count_missed_days(db)
            if db_member.day_time < 90 and today_num < 5 and count_days and db_member.period_failed == 0:
                db_member.missed_days += 1
            db_member.day_time = 0
        if today_num == week_reset_day:
            await send_stat(server_members)
            await create_members()
            for db_member in db_members:
                if db_member.week_time < 450 and count_days and db_member.period_failed == 0:
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
