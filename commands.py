

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
