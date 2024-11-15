import discord
from discord import app_commands
from discord.ext import commands
from time import perf_counter
from components.mlcompanion import MLCompanion
from components.embed_with_files import EmbedWithFiles


class CogCommands(commands.Cog):
    def __init__(self, bot: MLCompanion):
        self.bot: MLCompanion = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{__name__} carregou!')

    @app_commands.command(name='registrar',
                          description='Registra a sua conta Discord na base de dados do chatbot.')
    @app_commands.describe(matricula="Insira a matrícula presente em seu Moodle.")
    async def registrar(self, interaction: discord.Interaction, matricula: str):
        res = self.bot.general_manager.command_registrar_aluno(matricula, interaction.user.id)
        embeds = [embed_with_file.embed for embed_with_file in res]
        files = []
        for embed_with_file in res:
            for file in embed_with_file.files:
                files.append(file)
        await interaction.response.send_message(embeds=embeds, files=files, ephemeral=True)

    @app_commands.command(name='progresso',
                          description='Veja seu nível atual, experiência total e progresso até o próximo nível.')
    async def progresso(self, interaction: discord.Interaction):
        # time_start = perf_counter()
        res = self.bot.general_manager.command_mostrar_progresso_lv(interaction.user.id)
        embeds = [embed_with_file.embed for embed_with_file in res]
        files = []
        for embed_with_file in res:
            for file in embed_with_file.files:
                files.append(file)
        await interaction.response.send_message(embeds=embeds, files=files, ephemeral=True)
        # time_stop = perf_counter()
        # print(f"TEMPO: {time_stop - time_start} segundos!")

    @app_commands.command(name='pendencias',
                          description="Verifique quais atividades passadas você ainda não entregou.")
    async def pendencias(self, interaction: discord.Interaction):
        # time_start = perf_counter()
        res = self.bot.general_manager.command_mostrar_pendencias(interaction.user.id)
        await interaction.response.send_message(embed=res.embed, files=res.files, ephemeral=True)
        # time_stop = perf_counter()
        # print(f"TEMPO: {time_stop - time_start} segundos!")


async def setup(bot: MLCompanion):
    await bot.add_cog(CogCommands(bot))
