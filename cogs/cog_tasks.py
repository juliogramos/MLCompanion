import datetime
import time
from os import getenv
from typing import Final
import zoneinfo

import discord
from discord import app_commands
from discord.ext import commands, tasks
from components.mlcompanion import MLCompanion
from components.embed_with_files import EmbedWithFiles

TASK_TIMEZONE: Final[str] = getenv('TIMEZONE')
ENTREGA_HOUR: Final[int] = int(getenv('ENTREGA_HOUR'))
ENTREGA_MINUTE: Final[int] = int(getenv('ENTREGA_MINUTE'))
ENTREGA_SECOND: Final[int] = int(getenv('ENTREGA_SECOND'))
ENTREGA_TIME = datetime.time(hour=ENTREGA_HOUR,
                             minute=ENTREGA_MINUTE,
                             second=ENTREGA_SECOND,
                             tzinfo=zoneinfo.ZoneInfo(key=TASK_TIMEZONE))

RECOMMEND_HOUR: Final[int] = int(getenv('RECOMMEND_HOUR'))
RECOMMEND_MINUTE: Final[int] = int(getenv('RECOMMEND_MINUTE'))
RECOMMEND_SECOND: Final[int] = int(getenv('RECOMMEND_SECOND'))
RECOMMEND_TIME = datetime.time(hour=RECOMMEND_HOUR,
                             minute=RECOMMEND_MINUTE,
                             second=RECOMMEND_SECOND,
                             tzinfo=zoneinfo.ZoneInfo(key=TASK_TIMEZONE))


class CogTasks(commands.Cog):
    def __init__(self, bot: MLCompanion):
        self.bot: MLCompanion = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{__name__} carregou!')

    @tasks.loop(time=ENTREGA_TIME)
    async def task_entrega(self):
        now = time.time()
        await self.execute_entrega(now)
        await self.leaderboard()

    async def execute_entrega(self, entrega: float):
        res = self.bot.general_manager.task_entrega_atividade(entrega)
        for dic in res:
            for d_id, embed_list in dic.items():
                embeds = [embed_with_file.embed for embed_with_file in embed_list]
                files = []
                for embed_with_file in embed_list:
                    for file in embed_with_file.files:
                        files.append(file)
                user = await self.bot.fetch_user(d_id)
                await user.send(embeds=embeds, files=files)

    async def leaderboard(self):
        embeds_with_files = self.bot.general_manager.task_leaderboard()
        for discord_id, embed_with_files in embeds_with_files.items():
            user = await self.bot.fetch_user(discord_id)
            await user.send(embed=embed_with_files.embed, files=embed_with_files.files)

    @tasks.loop(time=RECOMMEND_TIME)
    async def task_recommend(self):
        now = time.time()
        await  self.recommend(now)

    async def recommend(self, today: float):
        embeds_with_files = self.bot.general_manager.task_recommend(today)
        for discord_id, embeds_with_files in embeds_with_files.items():
            user = await self.bot.fetch_user(discord_id)
            await user.send(embed=embeds_with_files.embed, files=embeds_with_files.files)

    @commands.command()
    async def start_entrega(self, _):
        self.task_entrega.start()
        print("Entrega Task Started!")

    @commands.command()
    async def start_recommend(self, _):
        self.task_recommend.start()
        print("Entrega Task Started!")


async def setup(bot: MLCompanion):
    await bot.add_cog(CogTasks(bot))
