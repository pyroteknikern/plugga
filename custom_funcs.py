from datetime import datetime, timedelta
from models import Base, Date, User
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker)
from sqlalchemy.future import select
from global_variables import TEXT_CHANNEL, SWE_TIME, FORMAT
import praw
import random
import os

engine = create_async_engine("sqlite+aiosqlite:///db.sqlite3",
                             connect_args={"check_same_thread": False})
SessionLocal = async_sessionmaker(engine)


async def gen_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    db = SessionLocal()
    return db

meme_max = 200
link_list = []


def get_link() -> str:
    global link_list
    if link_list == []:
        Scrape()
    link = random.choice(link_list)
    link_list.remove(link)
    return link


def Scrape():
    global link_list
    posturl_list = []
    posttitle_list = []
    filetypes = ["png", "jpg", "jpeg", "gif"]
    clientSecret = os.getenv("clientSecret")
    clientId = os.getenv("clientId")
    reddit = praw.Reddit(client_id=clientId,
                         client_secret=clientSecret,
                         user_agent=os.getenv("userAgent"))
    subreddit = reddit.subreddit("memes")
    top_post = subreddit.top("week", limit=meme_max)
    print("scraping...")
    for post in top_post:
        for sufix in filetypes:
            if post.url.endswith(sufix):
                posturl = post.url
                posttitle = post.title
                posturl_list.append(posturl)
                posttitle_list.append(posttitle)
                break
    print("scrape successful. " + str(len(posturl_list)))
    link_list = posturl_list


async def current_period(db) -> int:
    db_periods = (await db.execute(select(Date))).scalars().all()
    today = datetime.today().strftime(FORMAT)
    today = datetime.strptime(today, FORMAT)
    for db_period in db_periods:
        db_end = datetime.strptime(db_period.end_date, FORMAT)
        db_start = datetime.strptime(db_period.start_date, FORMAT)
        if today >= db_start and today < db_end:
            return db_period.period
    return 0


async def next_period(db) -> int:
    db_periods = (await db.execute(select(Date))).scalars().all()
    today = datetime.today().strftime(FORMAT)
    today = datetime.strptime(today, FORMAT)
    for db_period in db_periods:
        db_start = datetime.strptime(db_period.start_date, FORMAT)
        if today < db_start:
            return db_period.period
    return 0


# returns None if a period is not found
async def get_date_by_period(db, period: int):
    sql_statement = text(f'SELECT * FROM dates WHERE period={period}')
    res = await db.scalars(select(Date).from_statement(sql_statement))
    result = res.all()
    if not len(result):
        return None
    return result[0]


async def reset_user(db, username: str):
    db_member = await get_user_by_username(db, username)
    db_member.total_time = 0
    db_member.week_time = 0
    db_member.day_time = 0
    db_member.missed = 0
    db_member.challange_accepted = False


async def delete_prev_period_data(db):
    db_dates = (await db.execute(select(Date))).scalars().all()
    await db.delete(db_dates[0])
    db_members = (await db.execute(select(User))).scalars().all()
    for db_user in db_members:
        reset_user(db, db_user.name)


async def date_overlaps(db, ctx, start_date, end_date):
    db_dates = (await db.execute(select(Date))).scalars().all()
    start_date = datetime.strptime(start_date, FORMAT)
    end_date = datetime.strptime(end_date, FORMAT)
    for i, db_period in enumerate(db_dates):
        db_end = datetime.strptime(db_period.end_date, FORMAT)
        db_start = datetime.strptime(db_period.start_date, FORMAT)
        if start_date <= db_end and start_date >= db_start:
            await ctx.send(f"{start_date.strftime(FORMAT)} cannot be within period: {db_period.period}")
            return True
        if end_date <= db_end and end_date >= db_start:
            await ctx.send(f"{end_date.strftime(FORMAT)} cannot be within period: {db_period.period}")
            return True
        if end_date >= db_end and start_date <= db_start:
            await ctx.send(f"bloced by period: {db_period.period}")
            return True
    return False


async def get_user_by_username(db, user: str):
    sql_statement = text(f"SELECT * FROM users WHERE username='{user}'")
    res = await db.scalars(select(User).from_statement(sql_statement))
    result = res.all()
    if not len(result):
        return None
    return result[0]


async def period_info(db) -> str:
    message = ""
    cp = await current_period(db)
    cp_period = await get_date_by_period(db, cp)
    if cp is not False:
        cp_period_start = datetime.strptime(cp_period.start_date, FORMAT)
        cp_period_end = datetime.strptime(cp_period.end_date, FORMAT)
        cp_middle_date = cp_period_start + (cp_period_end - cp_period_start)/2

        message += "**Current period:**                   "
        message += f"{cp}\n"
        message += "**Period started at:**              "
        temp_str = f"{cp_period_start.strftime(FORMAT)}"
        message += temp_str
        message += "\n**Period middle date is:**      "
        temp_str = f"{cp_middle_date.strftime(FORMAT)}"
        message += temp_str
        message += "\n**Period ends at:**                    "
        temp_str = f"{cp_period_end.strftime(FORMAT)}"
        message += temp_str
        message += "\n*The above content may not be accurate, make sure to keep track on your own calander!*\n"
    else:
        np = await next_period(db)
        if np is False:
            message = "**No registered periods for the moment, please stand by (maybe relax) until next period!**"
    return message


async def send_stat(server_members, bot, ctx=None):
    db = await gen_db()
    if ctx is None:
        message = await period_info(db)
    else:
        message = ""
    channel = bot.get_channel(TEXT_CHANNEL)
    for server_member in server_members:
        if server_member.bot:
            continue
        db_member = await get_user_by_username(server_member.name, db)
        message += f"{server_member.mention}\n"
        if db_member is None:
            message += "Your name is not registerd\n"
            continue
        if ctx is not None:
            message += f"**Today:**\t\t\t\t{FORMAT_time(db_member.day_time)}\n"
        message += f"**This week:**\t\t{FORMAT_time(db_member.week_time)}\n"
        message += f"**Total:**\t\t\t\t  {FORMAT_time(db_member.total_time)}\n"
        message += f"**Missed days:**    {db_member.missed}\n"
        message += f"**Debt:**\t\t\t\t  {db_member.missed*150} kr\n"
    await db.close()
    if ctx is not None:
        await ctx.send(message)
    else:
        await channel.purge(limit=2)
        await channel.send(message)


def FORMAT_time(minutes):
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min"


def get_current_hour() -> int:
    return int(datetime.now(SWE_TIME).strftime("%H"))


async def is_tentap(db) -> bool:
    db_periods = (await db.execute(select(Date))).scalars().all()
    today = datetime.today().strftime(FORMAT)
    today = datetime.strptime(today, FORMAT)
    for db_period in db_periods:
        db_end = datetime.strptime(db_period.end_date, FORMAT)
        db_start = datetime.strptime(db_period.start_date, FORMAT)
        stop_date = db_end - timedelta(days=14)
        if today >= db_start and today < stop_date:
            return False
    return True
