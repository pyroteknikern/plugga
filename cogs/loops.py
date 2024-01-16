from discord.ext import tasks, commands
from datetime import date, datetime
from app.constants import (GUILD_ID,
                           DAY_RESET_TIME,
                           WEEK_RESET_DAY,
                           MIN_TIME_DAY,
                           MIN_TIME_WEEK,
                           FORMAT,
                           VOICE_CHANNEL)
from app.models import User
from app.custom_funcs import (get_user_by_username,
                              get_current_hour,
                              get_date_by_period,
                              is_tentap,
                              delete_prev_period_data,
                              current_period,
                              )

from app.gen_db import gen_db
from sqlalchemy.future import select
import logging

logging.basicConfig(filename="plugga_bot.log", level=logging.INFO)


class Tasks(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_time.start()
        self.once_every_hour.start()

    @tasks.loop(hours=1)
    async def once_every_hour(self):
        logging.info("Loop 1h")
        await create_members(self.bot)
        db = await gen_db()

        if get_current_hour() == DAY_RESET_TIME:
            await once_a_day(db, self.bot)

        await db.commit()
        await db.close()

    # gör om
    @tasks.loop(minutes=1)
    async def check_time(self):

        if get_current_hour() < 5:
            return

        db = await gen_db()
        channel = self.bot.get_channel(VOICE_CHANNEL)
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


# funcs
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
        await once_a_week(db)


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


async def create_members(bot):
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


async def setup(bot):
    await bot.add_cog(Tasks(bot))
