import random
import time


IMAGE_LIST = ["https://www.stockvault.net/data/2016/05/13/197535/preview16.jp"
              "g",
              "https://images.rawpixel.com/image_800/cHJpdmF0ZS9zdGF0aWMvaW1h"
              "Z2Uvd2Vic2l0ZS8yMDIyLTA0L2xyL3B4MTA4MzY2My1pbWFnZS1rd3Z3YmphdS"
              "5qcGc.jpg"
              ]
COOKIE_IMG_LINK = ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/"
                   "2019-11-29_14_52_43_The_interior_of_a_tin_of_McKenzie_%26_"
                   "Lloyds_Danish_Style_Butter_Cookies_in_the_Dulles_section_o"
                   "f_Sterling%2C_Loudoun_County%2C_Virginia.jpg/1200px-2019-1"
                   "1-29_14_52_43_The_interior_of_a_tin_of_McKenzie_%26_Lloyds"
                   "_Danish_Style_Butter_Cookies_in_the_Dulles_section_of_Ster"
                   "ling%2C_Loudoun_County%2C_Virginia.jpg")


async def motivate_0(ctx):

    await ctx.send(f"{IMAGE_LIST[random.randint(0, len(IMAGE_LIST)-1)]}")
    await ctx.send("see this puppy?")

    time.sleep(3)

    await ctx.send("if you don't study this week, I will kill it")


async def motivate_1(ctx):

    await ctx.send("If you don't study, I will find you and I will kill you")


async def motivate_2(ctx):

    await ctx.send("Here, have a cookie.\n"
                   f"{COOKIE_IMG_LINK}"
                   )
    time.sleep(2)

    await ctx.send("SIKE, you need to study!")
    await ctx.send("when you need to take a break, "
                   "maybe you can have one bite. maybe")


async def motivate_3(ctx):
    await ctx.send("NO!, Do it yourself!")
    await ctx.send("ok, fine!")
    await ctx.send("You can do this!")
