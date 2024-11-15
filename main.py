from typing import Final

import discord.ext.commands
from dotenv import load_dotenv
import os
import asyncio

from components.mlcompanion import MLCompanion
from managers.general_manager import GeneralManager

# Load from env
load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
MOODLE_TOKEN: Final[str] = os.getenv('MOODLE_TOKEN')
BASE_URL: Final[str] = os.getenv('BASE_URL')
COURSE_NAME: Final[str] = os.getenv('COURSE_NAME')
TIMEZONE: Final[str] = os.getenv('TIMEZONE')
CHANNEL: Final[int] = int(os.getenv('DISCORD_CHANNEL'))

# Bot Setup
bot = MLCompanion(DISCORD_TOKEN, CHANNEL)
general_manager = GeneralManager(MOODLE_TOKEN, BASE_URL, COURSE_NAME, TIMEZONE)

asyncio.run(bot.main(general_manager))
