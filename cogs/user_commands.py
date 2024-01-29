from datetime import datetime
from app.models import Date
from discord.ext import commands
from app.motivate_funcs import (
        motivate_0,
        motivate_1,
        motivate_2,
        motivate_3
        )
from app.date_funcs import (
        get_period_info,
        check_date_overlap,
        get_date_by_period,
        current_period,
        get_stat_message
        )
from app.custom_funcs import get_user_by_username
from app.constants import FORMAT
from app.gen_db import gen_db
from app.reddit import get_link
import logging
import random
import os


logging.basicConfig(filename="plugga_bot.log", level=logging.INFO)


class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="check-period")
    async def check_period(self, ctx):
        logging.info(f"check-period: {ctx.author.name}")
        db = await gen_db()
        message = await get_period_info(db)
        await ctx.send(message)
        await db.close()

    @commands.command(name="my-time")
    async def my_time(self, ctx):
        logging.info(f"my-time: {ctx.author.name}")
        await ctx.send(await get_stat_message(ctx.author.name))

    @commands.command(name="add-period")
    async def add_period(self, ctx, date):
        logging.info(f"add-period: {ctx.author.name}")

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

        if await check_date_overlap(db, ctx, start_date, end_date):
            await ctx.send("period is overlaping existing period")
            await db.close()
            return

        new_period = Date(start_date=start_date,
                          end_date=end_date,
                          period=period
                          )
        db.add(new_period)
        await db.commit()
        await db.close()
        await ctx.send(f"period was added\n{start_date}, {end_date}\n")

    @commands.command(name="meme")
    async def meme(self, ctx):
        logging.info(f"meme: {ctx.author.name}")
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

    @commands.command(name="motivate-me")
    async def motivate_me(self, ctx):
        logging.info(f"motivate-me: {ctx.author.name}")
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

    @commands.command(name="accept-challange")
    async def accept_challange(self, ctx):
        logging.info(f"accept-challange: {ctx.author.name}")
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
            await ctx.send('You are too late to join the current'
                           'period, sorry!')
            return

        if db_member.period_failed != 0:
            await db.close()
            await ctx.send('Error: 69\nlol get blocked!')
            return

        db_member.challange_accepted = True
        await ctx.send('Sucefully joined the chllange, best of luck!')
        await db.commit()
        await db.close()

    @commands.command(name="quit-challange")
    async def quit_challange(self, ctx):
        logging.info(f"quit-challange: {ctx.author.name}")
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

    @commands.command(name="delete")
    async def delete_member(self, ctx, name):
        logging.info(f"delete: {ctx.author.name}")
        db = await gen_db()
        db_member = await get_user_by_username(name, db)
        db_member.deleted = True
        await db.commit()
        await db.close()
        await ctx.send(f"{name} was deleted")

    @commands.command(name="undelete")
    async def undelete_member(ctx, name):
        logging.info(f"undelete: {ctx.author.name}")
        db = await gen_db()
        db_member = await get_user_by_username(name, db)
        db_member.deleted = False
        await db.commit()
        await db.close()
        await ctx.send(f"{name} was undeleted")


async def setup(bot):
    await bot.add_cog(Commands(bot))
