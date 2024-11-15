import json
from collections import OrderedDict
from components.aluno import Aluno


class GamificationManager:
    def __init__(self) -> None:
        self.exp_table: list[int] = []
        self.load_exp_table()

    def load_exp_table(self) -> None:
        with open('./jsons/exp_table.json', 'r', encoding='utf8') as f:
            exp_table = json.load(f)
            self.exp_table = exp_table['table']

    def get_level_progess(self, aluno: Aluno) -> int:
        xp_limit = self.exp_table[aluno.lv]
        xp_goal = xp_limit - aluno.xp
        return xp_goal

    def check_level_up(self, aluno: Aluno) -> bool:
        if aluno.xp >= self.exp_table[aluno.lv]:
            aluno.lv += 1
            return True
        return False

    def grant_xp(self, aluno: Aluno, xp_amount: int) -> bool:
        aluno.xp += xp_amount
        return self.check_level_up(aluno)

    def calculate_exp_from_assignment(self, alunos: list[Aluno], grades: list, exp: int) -> dict:
        exp_per_aluno = {}
        for aluno in alunos:
            exp_per_aluno[aluno.matricula] = {'exp': 0,
                                              'grade': 0.0}

        for grade in grades:
            new_grade = float(grade['grade'])
            percent = int(new_grade) * 10
            graded_aluno = None
            for aluno in alunos:
                if aluno.m_id == grade['userid']:
                    graded_aluno = aluno
                    break
            exp_amount = int((exp * percent) // 100)
            if exp_amount > exp_per_aluno[graded_aluno.matricula]['exp']:
                exp_per_aluno[graded_aluno.matricula]['exp'] = exp_amount
            if new_grade > exp_per_aluno[graded_aluno.matricula]['grade']:
                exp_per_aluno[graded_aluno.matricula]['grade'] = new_grade
        return exp_per_aluno

    def reward_exp_from_assignment(self, alunos: list[Aluno], grades: list, exp: int) -> dict:
        exp_per_aluno = self.calculate_exp_from_assignment(alunos, grades, exp)
        alunos_results = {}
        for aluno in alunos:
            alunos_results[aluno.matricula] = {
                'exp_granted': exp_per_aluno[aluno.matricula]['exp'],
                'grade': exp_per_aluno[aluno.matricula]['grade'],
                'leveled': self.grant_xp(aluno, exp_per_aluno[aluno.matricula]['exp']),
                'progress': self.get_level_progess(aluno)
            }
        return alunos_results

    def reward_exp_from_activity(self, alunos: list[Aluno], exp: int) -> dict:
        alunos_results = {}
        for aluno in alunos:
            alunos_results[aluno.matricula] = {
                'exp_granted': exp,
                'grade': None,
                'leveled': self.grant_xp(aluno, exp),
                'progress': self.get_level_progess(aluno)
            }
        return alunos_results

    def make_whole_leaderboard(self, alunos: list[Aluno]) -> dict:
        dic = {}
        for aluno in alunos:
            if aluno.xp not in dic.keys():
                dic[aluno.xp] = [aluno]
            else:
                dic[aluno.xp].append(aluno)
        leaderboard = dict(reversed(sorted(list(dic.items()))))
        return leaderboard

    # Key: Aluno, Values = {leaderboard: dict[categoria, comment], development: str}
    def make_leaderboards_per_student(self, alunos: list[Aluno], whole_leaderboard: dict) -> dict:
        leaderboards_per_student = {}
        top_5 = list(whole_leaderboard.keys())[:5]
        for aluno in alunos:
            personal_leaderboard = {}
            development = ""
            new_in_top_5 = False

            for categoria in top_5:
                comment = f"{len(whole_leaderboard[categoria])} aluno(s) nessa categoria"
                if aluno.xp == int(categoria):
                    comment += " - você está aqui!"
                    new_in_top_5 = True
                else:
                    comment += "."
                personal_leaderboard[categoria] = comment
            if not new_in_top_5:
                personal_leaderboard[aluno.xp] = "Você está aqui!"

            if new_in_top_5 and aluno.in_top_5:
                development = "Você se manteve no top 5, parabéns!"
            elif new_in_top_5 and not aluno.in_top_5:
                development = "Parabéns, você alcançou o top 5!"
                aluno.in_top_5 = True
            elif not new_in_top_5 and aluno.in_top_5:
                development = "Poxa, você saiu do top 5! Mas não se preocupe, você ainda pode se sair bem!"
                aluno.in_top_5 = False
            elif not new_in_top_5 and not aluno.in_top_5:
                development = "Parece que você ainda tem pendências! Se esforce para melhorar sua posição!"

            leaderboards_per_student[aluno.matricula] = {'leaderboard': personal_leaderboard,
                                                         'development': development}
        return leaderboards_per_student
