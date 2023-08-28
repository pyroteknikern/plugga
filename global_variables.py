from dotenv import load_dotenv
import os
import pytz

load_dotenv()

token = os.getenv('discordToken')
VOICE_CHANNEL = int(os.getenv('voiceChannel'))
GUILD_ID = int(os.getenv('guildId'))
TEXT_CHANNEL = int(os.getenv('textChannel'))

day_reset_time = 0
week_reset_day = 0

format = "%d-%m-%Y"
SWE_TIME = pytz.timezone("Europe/Stockholm")
