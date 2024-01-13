import os
from sqlalchemy.future import select
from datetime import datetime, date

from models import User, Date

from discord.ext import tasks

from create_bot import create_bot

from motivate_funcs import (motivate_0,
                            motivate_1,
                            motivate_2,
                            motivate_3)


from custom_funcs import (send_stat,
                          period_info,
                          gen_db,
                          date_overlaps,
                          get_date_by_period,
                          get_user_by_username,
                          current_period, get_current_hour,
                          delete_prev_period_data,
                          is_tentap,
                          get_link,
                          Scrape)

from global_variables import (GUILD_ID,
                              VOICE_CHANNEL,
                              token,
                              WEEK_RESET_DAY,
                              DAY_RESET_TIME,
                              FORMAT,
                              MIN_TIME_DAY,
                              MIN_TIME_WEEK)

import logging
import random

logging.basicConfig(filename="plugga_bot.log", level=logging.INFO)

bot = create_bot()


@bot.command(name="checkperiod")
async def display_period(ctx):
    db = await gen_db()
    message = await period_info(db)
    await ctx.send(message)
    await db.close()


@bot.command(name="mytime")
async def display_stat(ctx):
    await send_stat([ctx.author], bot, ctx=ctx)


@bot.command(name="period")
async def set_test_date(ctx, date):
    if ctx.channel.id != int(os.getenv("modChannel")):
        return
    a = date.split("-")
    start_date_list = a[0].split(",")
    end_date_list = a[1].split(",")
    period = int(a[2])

    start_date = (f"{str(start_date_list[0])}-"
                  f"{str(start_date_list[1])}-"
                  f"{str(start_date_list[2])}")

    end_date = (f"{str(end_date_list[0])}-"
                f"{str(end_date_list[1])}-"
                f"{str(end_date_list[2])}")

    res = True
    try:
        res = bool(datetime.strptime(start_date, FORMAT))
    except ValueError:
        res = False
    if not res:
        await ctx.send("this is not the correct FORMAT")
        return

    db = await gen_db()
    if await date_overlaps(db, ctx, start_date, end_date):
        await db.close()
        return
    new_start_date = Date(start_date=start_date,
                          end_date=end_date,
                          period=period
                          )
    db.add(new_start_date)
    await db.commit()
    await db.close()
    await ctx.send(f"period was added\n{start_date}, {end_date}\n")


@bot.command(name="meme")
async def meme(ctx):
    db = await gen_db()
    user = await get_user_by_username(db, ctx.author.name)
    if user.daily_meme_used:
        await ctx.send("You have used your daily meme today")
        await db.close()
        return
    link = get_link()
    await ctx.send(f"This is your daily meme:\n{link}")
    user.daily_meme_used = True
    await db.commit()
    await db.close()


@bot.command(name="test")
async def test(ctx):
    db = gen_db()
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


@bot.command(name="motivate-me")
async def MotivateIShall(ctx):
    num = random.randint(0, 3)
    match num:
        case 0:
            await motivate_0(ctx)
        case 1:
            await motivate_1(ctx)
        case 2:
            await motivate_2(ctx)
        case 3:
            await motivate_3(ctx)


@bot.command(name="accept-challange")
async def accept_challange(ctx):
    db = await gen_db()
    cp = await current_period(db)
    cp_period = await get_date_by_period(db, cp)
    cp_period_start = datetime.strptime(cp_period.start_date, FORMAT)
    cp_period_end = datetime.strptime(cp_period.end_date, FORMAT)
    cp_middle_date = cp_period_start + (cp_period_end - cp_period_start)/2
    today = datetime.today().strftime(FORMAT)
    today = datetime.strptime(today, FORMAT)
    db_member = await get_user_by_username(ctx.author.name, db)
    if today >= cp_middle_date:
        await db.close()
        await ctx.send('You are too late to join the current period, sorry!')
        return
    if db_member.period_failed != 0:
        await db.close()
        await ctx.send('Error: 69\nlol get blocked!')
        return
    db_member.challange_accepted = True
    await ctx.send('Sucefully joined the chllange, best of luck!')
    await db.commit()
    await db.close()


@bot.command(name="quit-challange")
async def quit_challange(ctx):
    db = await gen_db()
    cp = await current_period(db)
    db_member = await get_user_by_username(db, ctx.author.name)
    if not cp and db_member.period_failed != 0:
        await db.close()
        await ctx.send("there is not currently an active period")
        return
    db_member.challange_accepted = False
    db_member.period_failed = 2
    await ctx.send("I KNEW IT! \n jk ofcouse im a bot! I don't care!")
    await db.commit()
    await db.close()


@bot.command(name="delete")
async def delete_member(ctx, name):
    db = await gen_db()
    db_member = await get_user_by_username(name, db)
    db_member.deleted = True
    await db.commit()
    await db.close()
    await ctx.send(f"{name} was deleted")


@bot.command(name="undelete")
async def undelete_member(ctx, name):
    db = await gen_db()
    db_member = await get_user_by_username(name, db)
    db_member.deleted = False
    await db.commit()
    await db.close()
    await ctx.send(f"{name} was undeleted")


@bot.event
async def create_members():
    guild = bot.get_guild(GUILD_ID)
    memberList = guild.members
    db = await gen_db()
    for i, member in enumerate(memberList):
        if member.bot:
            continue
        if await get_user_by_username(db, member.name) is None:
            new_user = User(username=member.name,
                            total_time=0,
                            week_time=0,
                            day_time=0,
                            missed=0,
                            challange_accepted=False,
                            period_failed=0,
                            deleted=False,
                            daily_meme_used=False
                            )
            db.add(new_user)
            await db.commit()
            logging.info(f"Created new user: {member.name}")
    await db.close()


@tasks.loop(hours=1)
async def once_every_hour():
    logging.info("Loop 1h")
    await create_members()
    db = await gen_db()
    if get_current_hour() == DAY_RESET_TIME:
        await once_a_day(db, bot)
    await db.commit()
    await db.close()


async def once_a_day(db, bot):
    logging.info("once_a_day")
    db_members = (await db.execute(select(User))).scalars().all()
    today_num = date.today().weekday()
    await handle_end_of_period(db)
    reason = 0
    for db_member in db_members:
        logging.info(
                "In once_a_day(). "
                f"missed was not incremented due to reason: {reason}"
                )
        # daily resets
        db_member.day_time = 0
        db_member.daily_meme_used = False
        # increment missed days or not
        if not db_member.challange_accepted:
            reason = 1
            continue
        if today_num >= 5:
            reason = 2
            continue
        if (await is_tentap(db)):
            reason = 3
            continue
        if db_member.period_failed != 0:
            reason = 4
            continue
        if db_member.day_time >= MIN_TIME_DAY:
            reason = 5
            continue
        db_member.missed += 1

    if today_num == WEEK_RESET_DAY:
        await once_a_week(db, bot)


async def once_a_week(db, bot):
    logging.info("once_a_week")
    db_members = (await db.execute(select(User))).scalars().all()
    guild = bot.get_guild(GUILD_ID)
    server_members = guild.members
    reason = 0
    for db_member in db_members:
        logging.info(
                "In once_a_week(). "
                f"missed was not incremented due to reason: {reason}"
                )
        # weekly resets
        db_member.week_time = 0
        # increment missed days at end of week
        if not db_member.challange_accepted:
            reason = 1
            continue
        if (await is_tentap(db)):
            reason = 2
            continue
        if db_member.period_failed != 0:
            reason = 3
            continue
        if db_member.week_time >= MIN_TIME_WEEK:
            reason = 4
            continue
        db_member.missed += 1
    await db.commit()
    await send_stat(server_members, bot)


# går kanske att förbättra
async def handle_end_of_period(db):
    logging.info("End of period")
    db_members = (await db.execute(select(User))).scalars().all()
    today = datetime.today().strftime(FORMAT)
    today = datetime.strptime(today, FORMAT)
    cp = await current_period(db)
    cp_period = await get_date_by_period(db, cp)
    if cp_period is None:
        return

    cp_period_end = datetime.strptime(cp_period.end_date, FORMAT)
    if today < cp_period_end:
        return

    for db_member in db_members:
        if db_member.period_failed != 0:
            logging.info("decrementing period_failed for: "
                         f"{db_member.username}"
                         )
            db_member.period_failed -= 1
    delete_prev_period_data(db)


# gör om
@tasks.loop(minutes=1)
async def check_time():
    if get_current_hour() < 5:
        return
    db = await gen_db()
    channel = bot.get_channel(VOICE_CHANNEL)
    vc_members = channel.members
    for vc_member in vc_members:
        db_user = await get_user_by_username(db, vc_member.name)
        if db_user is None:
            continue
        db_user.day_time += 1
        db_user.week_time += 1
        db_user.total_time += 1
    await db.commit()
    await db.close()


@bot.event
async def on_ready():
    logging.info("Starting bot")
    Scrape()
    await create_members()

    check_time.start()
    once_every_hour.start()

bot.run(token)
