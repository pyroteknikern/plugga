from dotenv import load_dotenv
import os
import pytz

load_dotenv()

token = os.getenv('discordToken')
VOICE_CHANNEL = int(os.getenv('voiceChannel'))
GUILD_ID = int(os.getenv('guildId'))
TEXT_CHANNEL = int(os.getenv('textChannel'))

DAY_RESET_TIME = 4
WEEK_RESET_DAY = 0

MIN_TIME_DAY = 90
MIN_TIME_WEEK = 600

sqlWHERE__users__challage_accepted__o = "WHERE challange_accepted=1"
FORMAT = "%d-%m-%Y"
SWE_TIME = pytz.timezone("Europe/Stockholm")

HitList = ["https://www.stockvault.net/data/2016/05/13/197535/preview16.jpg",
            "https://images.rawpixel.com/image_800/cHJpdmF0ZS9zdGF0aWMvaW1hZ2Uvd2Vic2l0ZS8yMDIyLTA0L2xyL3B4MTA4MzY2My1pbWFnZS1rd3Z3YmphdS5qcGc.jpg"]
