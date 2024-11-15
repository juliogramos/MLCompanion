import discord
from discord import Embed, File
from components.aluno import Aluno
from components.embed_with_files import EmbedWithFiles
from components.atividade import Atividade, TipoAtividade


class ResponseManager:
    def error_not_registered(self):
        embed_unregistered = discord.Embed(title="Algo deu errado!",
                                           description='Opa, parece que você ainda não se registrou! '
                                                 'Por favor, efetue o seu registro com o comando /registrar')
        embed_unregistered.set_thumbnail(url="attachment://error_2.png")
        return EmbedWithFiles(embed_unregistered, ["./imgs/expressions/error_2.png"])

    def error_matricula_not_found(self):
        embed_not_found = discord.Embed(title="Algo deu errado!",
                                        description="Algo deu errado! Ou você digitou a sua matrícula incorretamente, "
                                                    "ou você não se matriculou nesse curso.")
        embed_not_found.set_thumbnail(url="attachment://error_2.png")
        return EmbedWithFiles(embed_not_found, ["./imgs/expressions/error_2.png"])

    def reply_registro(self, aluno: Aluno | None, overwrite: bool = False, xp_amount: int = 0) -> EmbedWithFiles:
        if not aluno:
            return self.error_matricula_not_found()

        embed_registro = discord.Embed(title="Registro concluído com sucesso!",
                                       description=f"Prazer em conhecer você, {aluno.nome_completo()}!")
        img = ""
        if overwrite:
            embed_registro.add_field(name="Aviso", value="Parece que alguém já registrou essa matrícula! "
                                                         "Você não ganhará experiência por esse registro. "
                                                         "Se você registrou a matrícula de um colega sem querer, "
                                                         "avise um colega para que vocês dois se registrem com as "
                                                         "matrículas corretas.")
            img = "error_1.png"
        else:
            embed_registro.add_field(name="Recompensa", value=f"Você recebeu {xp_amount} pontos de experiência!")
            img = "register.png"
        embed_registro.set_thumbnail(url="attachment://" + img)
        return EmbedWithFiles(embed_registro, ["./imgs/expressions/" + img])

    def reply_level_up(self, aluno: Aluno, progresso: int) -> EmbedWithFiles:
        embed_level_up = discord.Embed(
            title="Subiu de nível!",
            description=f"Parabéns! Você subiu para o nível {aluno.lv}!"
        )
        embed_level_up.add_field(name="Experiência total", value=f'{aluno.xp} pontos', inline=False)
        embed_level_up.add_field(name="Experiência para o próximo nível", value=f'{progresso} pontos', inline=False)
        embed_level_up.add_field(name="Recompensa", value="Parabéns, você ganhou uma nova badge!")
        embed_level_up.set_image(url=f"attachment://badge_{aluno.lv}.png")
        embed_level_up.set_thumbnail(url="attachment://congrats.png")
        return EmbedWithFiles(embed_level_up, ["./imgs/expressions/congrats.png",
                                               f"./imgs/badges/badge_{aluno.lv}.png"])

    def make_embed_with_files_for_each_badge(self, lv: int, graduated: bool) -> list[EmbedWithFiles]:
        embeds_with_files = []

        for i in range(1, lv + 1):
            new_embed = discord.Embed(title=f"Badge de nível {i}")
            new_embed.set_image(url=f"attachment://badge_{i}.png")
            embeds_with_files.append(EmbedWithFiles(new_embed, [f"./imgs/badges/badge_{i}.png"]))

        if graduated:
            embed_badge_graduated = discord.Embed(title="Badge de conclusão de curso")
            embed_badge_graduated.set_image(url="attachment://badge_graduate.png")
            embeds_with_files.append(EmbedWithFiles(embed_badge_graduated, ["./imgs/badges/badge_graduate.png"]))
        return embeds_with_files

    def reply_progresso_level(self, aluno: Aluno | None, graduated: bool, progresso: int = 0) -> list[EmbedWithFiles]:
        embed_progresso_level = discord.Embed(title=f"Seu progresso")
        embed_progresso_level.set_thumbnail(url="attachment://study.png")
        if aluno:
            embed_progresso_level.add_field(name="Nível", value=aluno.lv, inline=False)
            embed_progresso_level.add_field(name="Experiência total", value=f'{aluno.xp} pontos', inline=False)
            embed_progresso_level.add_field(name="Experiência para próximo nível",
                                            value=f'{progresso} pontos',
                                            inline=False)
            embed_progresso_level.set_footer(text="A seguir vou lhe mostrar todas as badges que obteve até agora.")
        else:
            return [self.error_not_registered()]
        other_embeds_with_files = self.make_embed_with_files_for_each_badge(aluno.lv, graduated)
        return [EmbedWithFiles(embed_progresso_level, ["./imgs/expressions/study.png"])] + other_embeds_with_files

    def reply_pendencias(self, pendencias: list[str]) -> EmbedWithFiles:
        embed_pendencias = discord.Embed(title="Suas pendências")
        embed_pendencias.set_footer(text="A atividade que você recebeu hoje não vai aparecer aqui, mas vai virar uma "
                                         "pendência caso você não a entregue até a próxima data!")
        if not pendencias:
            embed_pendencias.description = "Parabéns, você não tem nenhuma atividade pendente!"
            embed_pendencias.set_thumbnail(url="attachment://congrats.png")
            return EmbedWithFiles(embed_pendencias, ["./imgs/expressions/congrats.png"])
        else:
            embed_pendencias.description = "\n".join(pendencias)
            embed_pendencias.set_thumbnail(url="attachment://study.png")
            return EmbedWithFiles(embed_pendencias, ["./imgs/expressions/study.png"])

    def task_leaderboard(self, alunos: list[Aluno], leaderboards_per_student: dict) -> dict[int, EmbedWithFiles]:
        embeds = {}
        for aluno in alunos:
            embed_pessoal = discord.Embed(title="Progresso diário",
                                          description="Veja o que mudou:")
            placar = ""
            for categoria, comment in leaderboards_per_student[aluno.matricula]['leaderboard'].items():
                placar += f"{categoria} pontos de experiência:\n {comment}\n\n"
            embed_pessoal.add_field(name="Leaderboard", value=placar, inline=False)

            embed_pessoal.add_field(name="Sua avaliação",
                                    value=leaderboards_per_student[aluno.matricula]['development'],
                                    inline=False)
            embed_pessoal.set_thumbnail(url="attachment://leaderboard.png")
            embeds[aluno.discord_user] = EmbedWithFiles(embed_pessoal, ["./imgs/expressions/leaderboard.png"])
        return embeds

    def task_recommend(self, alunos: list[Aluno], atividade: Atividade) -> dict[int, EmbedWithFiles]:
        embeds = {}
        for aluno in alunos:
            msg = f"A atividade de hoje é: \n\n{atividade.nome}.\n\n"
            msg += "Você pode estudar usando os slides H5P, ou assistindo a aula em formato de vídeo."
            embed_recommend = discord.Embed(title="O que tem para hoje?",
                                            description=msg)
            if atividade.tipo == TipoAtividade.ATIVIDADE:
                embed_recommend.add_field(name="Orientações",
                                          value="Caso escolher a opção de H5P, você deve chegar até o último slide para"
                                                " que eu saiba que você assistiu a aula.\n\n"
                                                "Caso escolher o vídeo, apenas clicando no vídeo já é suficiente.\n\n"
                                                "Bons estudos!",
                                          inline=False)
            elif atividade.tipo == TipoAtividade.ENTREGA:
                embed_recommend.add_field(name="Orientações",
                                          value="Faça a atividade de acordo com as orientações, "
                                                "e depois envie no Moodle.\n\n"
                                                "Bons estudos!",
                                          inline=False)
            embed_recommend.set_thumbnail(url="attachment://study.png")
            embeds[aluno.discord_user] = EmbedWithFiles(embed_recommend, ["./imgs/expressions/study.png"])
        return embeds

    def task_entrega_assignment_submitted(self, alunos: list[Aluno], resultado: dict, nome: str) -> dict:
        embeds = {}
        alunos_dict = {}
        for aluno in alunos:
            alunos_dict[aluno.matricula] = aluno
        for matricula in resultado.keys():
            embeds[alunos_dict[matricula].discord_user] = []
            embed_entrega = discord.Embed(title="Hora da entrega!",
                                          description=f"Parabéns, você entregou a atividade: {nome}!")
            if resultado[matricula]['grade']:
                embed_entrega.add_field(name="Nota",
                                        value=f"A sua nota foi: {resultado[matricula]['grade']}",
                                        inline=False)
            embed_entrega.add_field(name="Recompensa",
                                    value=f"Você obteve {resultado[matricula]['exp_granted']} pontos de experiência")
            embed_entrega.set_thumbnail(url="attachment://relax.png")
            entrega_files = EmbedWithFiles(embed_entrega, ["./imgs/expressions/relax.png"])
            embeds[alunos_dict[matricula].discord_user].append(entrega_files)
            if resultado[matricula]['leveled']:
                embeds[alunos_dict[matricula].discord_user].append(
                    self.reply_level_up(alunos_dict[matricula], resultado[matricula]['progress'])
                )
        return embeds

    def task_entrega_assignment_not_submitted(self, alunos: list[Aluno], nome: str) -> dict:
        embeds = {}
        for aluno in alunos:
            embed_entrega = discord.Embed(title="Hora da entrega!",
                                          description=f"Poxa, parece que você não entregou a atividade: {nome}!")
            embed_entrega.set_thumbnail(url='attachment://sad.png')
            entrega_files = EmbedWithFiles(embed_entrega, ['./imgs/expressions/sad.png'])
            embeds[aluno.discord_user] = [entrega_files]
        return embeds


