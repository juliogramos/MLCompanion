import time
from datetime import datetime
import zoneinfo
from managers.request_manager import RequestManager
from managers.moodle_manager import MoodleManager
from managers.gamification_manager import GamificationManager
from managers.response_manager import ResponseManager
from components.aluno import Aluno
from components.atividade import Atividade, TipoAtividade
from components.embed_with_files import EmbedWithFiles
from discord import Member, Embed


class GeneralManager:
    def __init__(self, m_token: str, base_url: str, course_name: str, timezone: str) -> None:
        print("GeneralManager inicializando...")

        # Env imports
        self.m_token: str = m_token
        self.base_url: str = base_url
        self.course_name: str = course_name
        self.timezone = timezone

        # Managers setup
        self.request_manager: RequestManager = RequestManager(self.m_token, self.base_url)
        self.moodle_manager: MoodleManager = MoodleManager()
        self.gamification_manager: GamificationManager = GamificationManager()
        self.response_manager: ResponseManager = ResponseManager()

    def setup_course_id(self) -> None:
        response = self.request_manager.get_all_courses()
        course_id = None
        for course in response:
            if course['displayname'] == self.course_name:
                course_id = course['id']
                break
        if course_id:
            self.request_manager.set_course_id(course_id)
            print(f"Curso encontrado e salvo! O ID é: {course_id}.")
        else:
            raise Exception("O curso não foi encontrado. "
                            "Verifique se inseriu o nome do curso corretamente.")

    def setup_alunos(self) -> None:
        lista_alunos = self.request_manager.get_enrolled_users()
        self.moodle_manager.import_alunos(lista_alunos)
        self.moodle_manager.load_info_alunos()

    # O formato da atividade deve ser:
    # chatbot
    # &
    # nome atividade h5p
    # &
    # nome atividade lesson
    def import_atividades(self, timezone: str) -> None:
        if not self.moodle_manager.load_atividades(timezone):
            # Atividades H5P e Lesson
            eventos = self.request_manager.get_calendar_events()
            atividades_h5p = self.request_manager.get_h5p_activities()
            atividades_lesson = self.request_manager.get_lessons()
            entrega_assignments = self.request_manager.get_assignments()
            self.moodle_manager.import_atividades(eventos, atividades_h5p, atividades_lesson, entrega_assignments,
                                                  timezone)
            if not self.moodle_manager.atividades:
                raise Exception("Nenhuma atividade foi importada.")
            self.moodle_manager.save_atividades()
            nomes = ", ".join(atv.nome for atv in self.moodle_manager.atividades)
            print(f"As seguintes atividades foram importadas: {nomes}")

    def command_registrar_aluno(self, matricula: str, discord_user: int) -> list[EmbedWithFiles]:
        aluno, overwrite = self.moodle_manager.registrar_aluno(matricula, discord_user)
        res = [self.response_manager.reply_registro(aluno, overwrite, 5)]
        if aluno and not overwrite:
            if self.gamification_manager.grant_xp(aluno, 5):
                progresso = self.gamification_manager.get_level_progess(aluno)
                res.append(self.response_manager.reply_level_up(aluno, progresso))
        self.moodle_manager.save_info_alunos()
        return res

    def command_mostrar_progresso_lv(self, discord_id: int) -> list[EmbedWithFiles]:
        aluno = self.moodle_manager.find_aluno_by_discord(discord_id)
        if aluno:
            xp_goal = self.gamification_manager.get_level_progess(aluno)
            graduated = self.is_course_over(time.time())
            res = self.response_manager.reply_progresso_level(aluno, graduated, xp_goal)
        else:
            res = [self.response_manager.error_not_registered()]
        return res

    def command_mostrar_pendencias(self, discord_id: int) -> EmbedWithFiles:
        aluno = self.moodle_manager.find_aluno_by_discord(discord_id)
        if aluno:
            pendencias = self.moodle_manager.verificar_pendencias(aluno, self.timezone)
            res = self.response_manager.reply_pendencias(pendencias)
        else:
            res = self.response_manager.error_not_registered()
        return res

    def entrega_uma_atividade(self, atividade: Atividade) -> dict:
        if atividade.tipo == TipoAtividade.ATIVIDADE:
            h5p_response = self.request_manager.get_h5p_attempts(atividade.h5p_id)
            lesson_reponse = self.request_manager.get_lesson_attempts(atividade.lesson_id)
            submitted, not_submitted, xp_amount = self.moodle_manager.entrega_atividade(
                atividade.h5p_id, atividade.lesson_id, h5p_response, lesson_reponse)
            alunos_results = self.gamification_manager.reward_exp_from_activity(submitted, xp_amount)
            embeds_submitted = self.response_manager.task_entrega_assignment_submitted(
                submitted, alunos_results, atividade.nome
            )
            embeds_not_submitted = self.response_manager.task_entrega_assignment_not_submitted(
                not_submitted, atividade.nome
            )
            return embeds_submitted | embeds_not_submitted
        elif atividade.tipo == TipoAtividade.ENTREGA:
            submissions = self.request_manager.get_assignment_submissions(atividade.assignment_id)
            submitted, not_submitted = self.moodle_manager.check_alunos_in_submissions(submissions)
            submitted = self.moodle_manager.check_alunos_already_completed_and_include(submitted, atividade)
            for aluno in submitted:
                self.moodle_manager.include_aluno_in_assignment_submitted(aluno, atividade)
            self.moodle_manager.save_atividades()
            embeds_submitted = {}
            if submitted:
                grades = self.request_manager.get_assingment_grades(atividade.assignment_id)
                alunos_results = self.gamification_manager.reward_exp_from_assignment(submitted, grades, atividade.xp)
                embeds_submitted = self.response_manager.task_entrega_assignment_submitted(
                    submitted, alunos_results, atividade.nome)
            embeds_not_submitted = self.response_manager.task_entrega_assignment_not_submitted(
                not_submitted, atividade.nome)
            return embeds_submitted | embeds_not_submitted

    def task_entrega_atividade(self, entrega: float) -> list:
        lista_atividades = self.moodle_manager.get_activities_on_before_entrega(entrega, self.timezone)
        lista_embeds = []
        for atividade in lista_atividades:
            lista_embeds.append(self.entrega_uma_atividade(atividade))
        self.moodle_manager.save_info_alunos()
        return lista_embeds

    def task_leaderboard(self) -> dict[int, EmbedWithFiles]:
        alunos = self.moodle_manager.get_alunos_with_discord()
        whole_leaderboard = self.gamification_manager.make_whole_leaderboard(alunos)
        leaderboards_per_student = self.gamification_manager.make_leaderboards_per_student(alunos, whole_leaderboard)
        self.moodle_manager.save_info_alunos()
        responses = self.response_manager.task_leaderboard(alunos, leaderboards_per_student)
        return responses

    def task_recommend(self, today: float) -> dict[int, EmbedWithFiles]:
        alunos = self.moodle_manager.get_alunos_with_discord()
        atividade = self.moodle_manager.get_todays_activity(today, self.timezone, True)
        embeds = self.response_manager.task_recommend(alunos, atividade)
        return embeds

    def is_course_over(self, current_time: float) -> bool:
        latest_entrega = self.moodle_manager.get_latest_entrega()
        if current_time > latest_entrega:
            return True


    def setup(self):
        self.setup_course_id()
        self.setup_alunos()
        self.import_atividades(self.timezone)
