import os
from typing import Final, Any

import discord
from discord.ext import commands
from discord.ext.commands import Context, errors

from managers.general_manager import GeneralManager


class MLCompanion(commands.Bot):
    def __init__(self, token: str, channel: int):
        # Setup básico
        self.token: Final[str] = token
        self.channel: Final[int] = channel
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True  # NOQA
        super().__init__(command_prefix='!', intents=intents)

        # Manager setup (vai ser feito no main)
        self.general_manager: GeneralManager | None = None

    async def load_cogs(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")

    async def on_ready(self):
        print(f"{self.user.name} logado!")
        channel = self.get_channel(self.channel)
        await channel.send("Ligou!")
        try:
            synced_commands = await self.tree.sync()
            print(f'{len(synced_commands)} comandos sincronizados.')
        except Exception as e:
            print(f"A sincronização de commandos resultou em um erro: {e}")

    async def on_tree_error(self, _, error: discord.app_commands.AppCommandError):
        print(error)

    async def custom_command_error(self, _, exception) -> None:
        print(exception)

    async def main(self, general_manager: GeneralManager):
        async with self:
            # Manager setup
            self.general_manager = general_manager
            self.general_manager.setup()

            # Bot load (start tem que ser último)
            await self.load_cogs()
            self.tree.on_error = self.on_tree_error
            self.on_command_error = self.custom_command_error
            await self.start(self.token)
