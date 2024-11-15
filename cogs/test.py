import discord
from discord.ext import commands


class Test(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{__name__} carregou!')

    @commands.command()
    async def ping(self, ctx: discord.ext.commands.Context):
        ping_embed = discord.Embed(title="Ping", description="Latency in ms", color=discord.Color.blue())
        ping_embed.add_field(name=f"Latência de {self.bot.user.name}: ",
                             value=f"{round(self.bot.latency * 1000)}ms.", inline=False)
        await ctx.send(embed=ping_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Test(bot))
