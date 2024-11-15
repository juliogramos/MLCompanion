import json
import os.path

from components.aluno import Aluno
from components.atividade import Atividade, TipoAtividade
from discord import Member
from re import sub
from datetime import datetime, timedelta
import zoneinfo


class MoodleManager:
    def __init__(self) -> None:
        self.alunos: dict[str, Aluno] = {}  # Key é a matrícula
        self.atividades: list[Atividade] = []
        self.alunos_id_lookup: dict[str, str] = {}  # ID -> Matrícula

    def import_alunos(self, lista_alunos: dict) -> None:
        lookup_list = []
        for aluno in lista_alunos:
            nome = aluno['firstname']
            sobrenome = aluno['lastname']
            m_id = aluno['id']
            for cf in aluno['customfields']:
                if cf['shortname'] == "Matricula":
                    matricula = cf['value']
                    break
            else:
                raise Exception("Não existe matrícula?")
            novo_aluno = Aluno(matricula, m_id, nome, sobrenome)
            self.alunos[matricula] = novo_aluno
            lookup_list.append((aluno['id'], matricula))
            print(f"Aluno {novo_aluno} obtido!")

        for aluno_id, aluno_matricula in lookup_list:
            self.alunos_id_lookup[aluno_id] = aluno_matricula

    def import_h5p_video_atividades(self,
                                    chaves: list[str],
                                    h5p_activities: list,
                                    lesson_activities: list,
                                    timestamp: float,
                                    timezone: str) -> Atividade:
        if chaves[3] == "H5P_Video":
            exp = int(chaves[1])
            h5p_id, lesson_id, nome = None, None, None
            for activity in h5p_activities:
                if chaves[4] == activity['name']:
                    h5p_id = activity['id']
                    nome = chaves[4]
                    break
            for activity in lesson_activities:
                if chaves[5] == activity['name']:
                    lesson_id = activity['id']
                    break
            if lesson_id is None or h5p_id is None:
                raise Exception(f"Erro: Atividade {chaves[4]} não encontrada.")
            entrega = datetime.fromtimestamp(timestamp).replace(tzinfo=zoneinfo.ZoneInfo(key=timezone))
            nova_atividade = Atividade(nome, TipoAtividade.ATIVIDADE, entrega, exp, h5p_id, lesson_id)
            return nova_atividade

    def import_assignment_entregas(self, chaves: list[str], assignments: list, timestamp: float, timezone: str):
        exp = int(chaves[1])
        assignment_id, nome = None, None
        for assignment in assignments:
            if chaves[3] == assignment['name']:
                assignment_id = assignment['id']
                nome = assignment['name']
                break
        if assignment_id is None:
            raise Exception(f"Erro: Entrega {chaves[3]} não encontrada.")
        entrega = datetime.fromtimestamp(timestamp).replace(tzinfo=zoneinfo.ZoneInfo(key=timezone))
        nova_entrega = Atividade(nome, TipoAtividade.ENTREGA, entrega, exp, assignment_id=assignment_id)
        return nova_entrega

    def import_atividades(self, eventos: list, h5p_activities: list, lesson_activities: list, assignments: list,
                          timezone: str) -> None:
        for evento in eventos:
            if evento['eventtype'] == 'course':
                chaves = sub('<[^<]+?>', '', evento['description']).split('&amp;')
                if chaves[0] != 'Chatbot':
                    continue
                # COLOCAR SUPORTE PARA OUTROS TIPOS DE ATIVIDADE
                if chaves[2] == "Atividade":
                    self.atividades.append(self.import_h5p_video_atividades(
                        chaves, h5p_activities,  lesson_activities, evento['timestart'], timezone))
                elif chaves[2] == "Entrega":
                    self.atividades.append((self.import_assignment_entregas(
                        chaves, assignments, evento['timestart'], timezone
                    )))

    def save_atividades(self):
        backup_data = []
        for atividade in self.atividades:
            backup_data.append(atividade.serialize())
        with open('./jsons/backup_atividades.json', 'w', encoding='utf8') as f:
            json.dump({'atividades': backup_data}, f, ensure_ascii=False)

    def load_atividades(self, timezone: str) -> bool:
        try:
            with open('./jsons/backup_atividades.json', 'r', encoding='utf8') as f:
                backup_data = json.load(f)
                for atividade in backup_data['atividades']:
                    nova_atividade = Atividade(
                        atividade['nome'],
                        TipoAtividade(atividade['tipo']),
                        datetime.fromtimestamp(atividade['entrega']).replace(tzinfo=zoneinfo.ZoneInfo(key=timezone)),
                        atividade['xp'],
                        atividade['h5p_id'],
                        atividade['lesson_id'],
                        atividade['assignment_id']
                    )
                    nova_atividade.matriculas_alunos = atividade['matriculas_alunos']
                    self.atividades.append(nova_atividade)
                    print(f"Atividade importada do backup: {nova_atividade.nome}")
                return True
        except FileNotFoundError:
            print('Backup de atividades não localizado! Criando...')
            return False

    # Apenas salva o discord já que vai dar fetch nos alunos de qualquer jeito
    def save_info_alunos(self) -> None:
        backup_data = {}
        for aluno in self.alunos.values():
            if aluno.discord_user != -1:
                backup_data[aluno.matricula] = aluno.serialize()
        with open('./jsons/backup_alunos.json', 'w', encoding='utf8') as f:
            json.dump(backup_data, f, ensure_ascii=False)

    def load_info_alunos(self) -> None:
        try:
            with open('./jsons/backup_alunos.json', 'r', encoding='utf8') as f:
                backup_data = json.load(f)
                for matricula, backup_aluno in backup_data.items():
                    self.alunos[matricula].discord_user = backup_aluno['discord_user']
                    self.alunos[matricula].lv = backup_aluno['lv']
                    self.alunos[matricula].xp = backup_aluno['xp']
                    self.alunos[matricula].in_top_5 = backup_aluno['in_top_5']
                    print(f'Registro de {self.alunos[matricula]} recuperado do backup!')
        except FileNotFoundError:
            print('Backup de alunos não localizado! Criando...')
            with open('./jsons/backup_alunos.json', 'w', encoding='utf8') as f:
                json.dump({}, f, ensure_ascii=False)

    def find_aluno_by_discord(self, discord_id: int) -> Aluno | None:
        for matricula, aluno in self.alunos.items():
            if aluno.discord_user == discord_id:
                return aluno
        else:
            return None

    def get_alunos_with_discord(self) -> list[Aluno]:
        alunos = []
        for aluno in self.alunos.values():
            if aluno.discord_user != -1:
                alunos.append(aluno)
        return alunos

    def get_aluno_by_moodle_id(self, moodle_id: str) -> Aluno | None:
        for aluno in self.alunos.values():
            if aluno.m_id == moodle_id:
                return aluno
        else:
            return None

    def get_atividade_xp(self, h5p_id) -> int:
        for atividade in self.atividades:
            if atividade.h5p_id == h5p_id:
                return atividade.xp
        else:
            raise Exception("Atividade não encontrada.")

    def get_atividade_by_id(self, h5p_id: int, lesson_id: int) -> Atividade:
        for atividade in self.atividades:
            if h5p_id == atividade.h5p_id or lesson_id == atividade.lesson_id:
                return atividade
        else:
            raise Exception("Atividade não existe.")

    def check_alunos_in_h5p_response(self, response: list, atividade: Atividade) -> list:
        alunos_list = []
        for aluno_attempts in response:
            if not aluno_attempts["attempts"]:
                continue
            matricula = self.alunos_id_lookup[aluno_attempts["userid"]]
            alunos_list.append(matricula)
        return alunos_list

    # Modifica a lista de entrada, então não retorna
    def check_alunos_in_lesson_response(self, response: list, atividade: Atividade, lista_alunos: list) -> None:
        for aluno_attempts in response:
            matricula = self.alunos_id_lookup[aluno_attempts["id"]]
            if matricula not in lista_alunos:
                lista_alunos.append(matricula)

    def check_alunos_already_completed_and_include(self, alunos: list[Aluno], atividade: Atividade) -> list[Aluno]:
        new_lista_alunos = []
        for aluno in alunos:
            if aluno.matricula not in atividade.matriculas_alunos:
                new_lista_alunos.append(aluno)
                atividade.matriculas_alunos.append(aluno.matricula)
        return new_lista_alunos

    def get_lists_alunos_completed_incomplete(self, matriculas: list) -> (
            tuple)[list[Aluno], list[Aluno]]:
        alunos_completed = []
        alunos_incomplete = []
        for matricula, aluno in self.alunos.items():
            if aluno.discord_user == -1:
                continue
            if matricula in matriculas:
                alunos_completed.append(aluno)
            elif matricula not in matriculas:
                alunos_incomplete.append(aluno)
        return alunos_completed, alunos_incomplete

    # Retorno: [nome do aluno | None, Sobreescrveu?]
    def registrar_aluno(self, matricula: str, discord_user: int) -> tuple[Aluno | None, bool]:
        aluno = None
        overwrite = False
        if matricula in self.alunos.keys():
            if self.alunos[matricula].discord_user != -1:
                overwrite = True
            self.alunos[matricula].discord_user = discord_user
            aluno = self.alunos[matricula]
            print(f"Aluno {aluno.nome_completo()} registrado com sucesso!")
        return aluno, overwrite

    def verificar_pendencias(self, aluno: Aluno, timezone: str) -> list[str]:
        pendencias = []
        for atividade in self.atividades:
            if atividade.entrega >= datetime.now().replace(tzinfo=zoneinfo.ZoneInfo(key=timezone)):
                break
            if aluno.matricula not in atividade.matriculas_alunos:
                pendencias.append(atividade.nome)
        return pendencias

    def check_alunos_in_submissions(self, submissions: list) -> tuple[list[Aluno], list[Aluno]]:
        alunos = self.get_alunos_with_discord()
        submitted = []
        not_submitted = []
        for aluno in alunos:
            did_submit = False
            for submission in submissions:
                if submission['userid'] == aluno.m_id and submission['gradingstatus'] == 'graded':
                    did_submit = True
                    break
            if did_submit:
                submitted.append(aluno)
            else:
                not_submitted.append(aluno)
        return submitted, not_submitted

    def include_aluno_in_assignment_submitted(self, aluno: Aluno, atividade: Atividade) -> None:
        if aluno.matricula not in atividade.matriculas_alunos:
            atividade.matriculas_alunos.append(aluno.matricula)

    def entrega_atividade(self, h5p_id: int, lesson_id: int,
                          h5p_response: list, lesson_response: list) -> tuple[list[Aluno], list[Aluno], int]:
        atividade = self.get_atividade_by_id(h5p_id, lesson_id)
        lista_alunos = self.check_alunos_in_h5p_response(h5p_response, atividade)
        self.check_alunos_in_lesson_response(lesson_response, atividade, lista_alunos)
        alunos_completed, alunos_incomplete = self.get_lists_alunos_completed_incomplete(lista_alunos)
        alunos_completed = self.check_alunos_already_completed_and_include(alunos_completed, atividade)
        self.save_atividades()
        xp_amount = atividade.xp
        return alunos_completed, alunos_incomplete, xp_amount

    def get_activity_by_entrega(self, entrega: float, timezone: str) -> Atividade:
        # MUDAR PARA O DIA ATUAL
        data_entrega = datetime.fromtimestamp(entrega).replace(tzinfo=zoneinfo.ZoneInfo(key=timezone))
        for atividade in self.atividades:
            if atividade.entrega.date() == data_entrega.date():
                return atividade
        else:
            raise Exception("Atividade não encontrada para hoje")

    def get_activities_on_before_entrega(self, entrega: float, timezone: str) -> list[Atividade]:
        lista_atividades = []
        data_entrega = datetime.fromtimestamp(entrega).replace(tzinfo=zoneinfo.ZoneInfo(key=timezone))
        for atividade in self.atividades:
            if atividade.entrega.date() <= data_entrega.date():
                lista_atividades.append(atividade)
        if not lista_atividades:
            raise Exception("Atividade não encontrada para hoje")
        return lista_atividades

    def get_latest_entrega(self) -> float:
        entregas = []
        for atividade in self.atividades:
            entregas.append(atividade.entrega.timestamp())
        return max(entregas)

    def get_todays_activity(self, today: float, timezone: str, debug: bool = False) -> Atividade:
        today_date = datetime.fromtimestamp(today).replace(tzinfo=zoneinfo.ZoneInfo(key=timezone))
        today_activity = None
        for atividade in self.atividades:
            if today_date.date() == atividade.entrega.date():
                today_activity = atividade
                break
        if today_activity:
            return today_activity
        else:
            if debug:
                return self.atividades[-1]
            else:
                raise Exception("Nenhuma atividade para hoje!")
