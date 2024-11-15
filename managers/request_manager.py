import requests
import json


class RequestManager:
    def __init__(self, m_token: str, base_url: str):
        self.m_token: str = m_token
        self.base_url: str = base_url + f'wstoken={self.m_token}' + f'&moodlewsrestformat=json'
        self.course_id: int | None = None

    def set_course_id(self, course_id: int):
        self.course_id = course_id

    def get_all_courses(self):
        func = 'core_course_get_courses'
        url = self.base_url + f'&wsfunction={func}'
        response = requests.get(url).json()
        return response

    def get_enrolled_users(self):
        if self.course_id is None:
            raise Exception("ID não definido. Use get_course.")
        func = 'core_enrol_get_enrolled_users'
        url = self.base_url + f'&wsfunction={func}' + f'&courseid={self.course_id}'
        response = requests.post(url).json()
        if len(response) == 0:
            raise Exception("O curso não possui nenhum aluno matriculado")
        return response

    def get_h5p_attempts(self, h5pactivityid: int) -> list:
        if self.course_id is None:
            raise Exception("ID não definido. Use get_course.")
        func = "mod_h5pactivity_get_attempts"
        url = self.base_url + f'&wsfunction={func}' + f'&h5pactivityid={h5pactivityid}'
        response = requests.post(url).json()
        return response["usersattempts"]

    def get_lesson_attempts(self, lessonid: int) -> list:
        if self.course_id is None:
            raise Exception("ID não definido. Use get_course.")
        func = 'mod_lesson_get_attempts_overview'
        url = self.base_url + f'&wsfunction={func}' + f'&lessonid={lessonid}'
        response = requests.post(url).json()
        if "data" not in response.keys():
            return []
        return response["data"]["students"]

    def get_calendar_events(self):
        if self.course_id is None:
            raise Exception("ID não definido. Use get_course.")
        func = 'core_calendar_get_calendar_events'
        url = self.base_url + f'&wsfunction={func}' + f'&events[courseids][0]={self.course_id}'
        response = requests.post(url).json()
        return response['events']

    def get_h5p_activities(self):
        if self.course_id is None:
            raise Exception("ID não definido. Use get_course.")
        func = 'mod_h5pactivity_get_h5pactivities_by_courses'
        url = self.base_url + f'&wsfunction={func}' + f'&courseids[0]={self.course_id}'
        response = requests.post(url).json()
        return response['h5pactivities']

    def get_lessons(self):
        if self.course_id is None:
            raise Exception("ID não definido. Use get_course.")
        func = 'mod_lesson_get_lessons_by_courses'
        url = self.base_url + f'&wsfunction={func}' + f'&courseids[0]={self.course_id}'
        response = requests.post(url).json()
        return response['lessons']

    def get_assignments(self):
        if self.course_id is None:
            raise Exception("ID não definido. Use get_course.")
        func = 'mod_assign_get_assignments'
        url = self.base_url + f'&wsfunction={func}' + f'&courseids[0]={self.course_id}'
        response = requests.post(url).json()
        return response['courses'][0]['assignments']

    def get_assignment_submissions(self, assignment_id: int):
        if self.course_id is None:
            raise Exception("ID não definido. Use get_course.")
        func = 'mod_assign_get_submissions'
        url = self.base_url + f'&wsfunction={func}' + f'&assignmentids[0]={assignment_id}'
        response = requests.post(url).json()
        return response['assignments'][0]['submissions']

    def get_assingment_grades(self, assignment_id: int):
        if self.course_id is None:
            raise Exception("ID não definido. Use get_course.")
        func = 'mod_assign_get_grades'
        url = self.base_url + f'&wsfunction={func}' + f'&assignmentids[0]={assignment_id}'
        response = requests.post(url).json()
        return response['assignments'][0]['grades']
