from datetime import datetime, timedelta
from models import Base, Date, User
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker)
from sqlalchemy.future import select
from global_variables import TEXT_CHANNEL, SWE_TIME
from create_bot import create_bot

engine = create_async_engine("sqlite+aiosqlite:///db.sqlite3",
                             connect_args={"check_same_thread": False})
SessionLocal = async_sessionmaker(engine)

bot = create_bot()


async def gen_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    db = SessionLocal()
    return db


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
