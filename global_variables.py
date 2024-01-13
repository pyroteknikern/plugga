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

