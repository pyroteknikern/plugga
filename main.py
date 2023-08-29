import os
from sqlalchemy.future import select
from datetime import datetime, date

from models import User, Date

from discord.ext import tasks

from create_bot import create_bot
from custom_funcs import send_stat, make_msg_times, gen_db, date_overlaps, get_date_by_period, get_user_by_username, current_period, get_current_hour, delete_prev_period_data, count_missed_days

from global_variables import GUILD_ID, VOICE_CHANNEL, token, week_reset_day, day_reset_time, format

bot = create_bot()


@bot.command(name="checkperiod")
async def display_period(ctx):
    db = await gen_db()
    message = await make_msg_times(db)
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
    start_date = f"{str(start_date_list[0])}-"
    start_date += f"{str(start_date_list[1])}-"
    start_date += f"{str(start_date_list[2])}"

    end_date = f"{str(end_date_list[0])}-"
    end_date += f"{str(end_date_list[1])}-"
    end_date += f"{str(end_date_list[2])}"

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


@bot.command(name="accept-challange")
async def accept_challange(ctx):
    db = await gen_db()
    cp = await current_period(db)
    cp_period = await get_date_by_period(db, cp)
    cp_period_start = datetime.strptime(cp_period.start_date, format)
    cp_period_end = datetime.strptime(cp_period.end_date, format)
    cp_middle_date = cp_period_start + (cp_period_start - cp_period_end)/2
    today = datetime.today().strftime(format)
    today = datetime.strptime(today, format)
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
        cp = await current_period(db)
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
            await send_stat(server_members, bot)
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
