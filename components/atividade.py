from datetime import datetime
from enum import IntEnum


class TipoAtividade(IntEnum):
    ATIVIDADE = 1
    ENTREGA = 2


class Atividade:
    def __init__(self, nome: str, tipo: TipoAtividade, entrega: datetime, xp: int,
                 h5p_id: int = -1, lesson_id: int = -1, assignment_id: int = -1):
        self.nome: str = nome
        self.tipo: TipoAtividade = tipo
        self.entrega: datetime = entrega
        self.h5p_id: int = h5p_id
        self.lesson_id: int = lesson_id
        self.assignment_id: int = assignment_id
        self.xp: int = xp
        self.matriculas_alunos: list[str] = []

    def serialize(self) -> dict:
        atv_data = {
            'nome': self.nome,
            'tipo': int(self.tipo),
            'entrega': self.entrega.timestamp(),
            'xp': self.xp,
            'h5p_id': self.h5p_id,
            'lesson_id': self.lesson_id,
            'assignment_id': self.assignment_id,
            'matriculas_alunos': self.matriculas_alunos
        }
        return atv_data
