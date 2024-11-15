from discord import Member


class Aluno:
    def __init__(self, matricula: str, m_id: str, first_name: str, last_name: str):
        self.matricula: str = matricula
        self.m_id: str = m_id
        self.xp: int = 0
        self.lv: int = 0
        self.nome: str = first_name
        self.sobrenome: str = last_name
        self.discord_user: int = -1
        self.in_top_5: bool = False

    def nome_completo(self) -> str:
        return self.nome + " " + self.sobrenome

    def serialize(self) -> dict:
        novo_aluno = {
            'discord_user': self.discord_user,
            'lv': self.lv,
            'xp': self.xp,
            'in_top_5': self.in_top_5
        }
        return novo_aluno

    def __str__(self):
        return f'{self.nome_completo()} ({self.matricula})'
