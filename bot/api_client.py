import os

import requests


class ApiClient:
    def __init__(self, base_url=None, token=None):
        self.base_url = base_url or os.getenv('BACKEND_URL', 'http://localhost:8000')
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Token {token}'})
        self.session.auth = (os.getenv('API_USER', 'admin'), os.getenv('API_PASS', 'admin'))

    def get(self, path, params=None):
        return self.session.get(f'{self.base_url}/api{path}', params=params)

    def post(self, path, data=None):
        return self.session.post(f'{self.base_url}/api{path}', json=data or {})

    def patch(self, path, data=None):
        return self.session.patch(f'{self.base_url}/api{path}', json=data or {})

    # --- Users ---
    def get_user_by_telegram(self, telegram_id):
        resp = self.get('/users/', params={'telegram_id': telegram_id})
        if resp.status_code == 200 and resp.json().get('results'):
            return resp.json()['results'][0]
        return None

    def get_users(self, params=None):
        return self.get('/users/', params=params)

    def get_students_by_class(self, class_id):
        return self.get('/users/', params={'role': 'student', 'student_class': class_id})

    def get_teachers(self):
        return self.get('/users/', params={'role': 'teacher'})

    # --- Classes ---
    def get_classes(self):
        return self.get('/classes/')

    # --- Subjects ---
    def get_subjects(self):
        return self.get('/subjects/')

    # --- Lessons / Schedule ---
    def get_lessons(self, params=None):
        return self.get('/lessons/', params=params)

    def get_schedule(self, user_id, role):
        params = {}
        if role == 'teacher':
            params['teacher'] = user_id
        elif role == 'student':
            resp = self.get(f'/users/{user_id}/')
            if resp.status_code != 200:
                return resp
            student = resp.json()
            class_id = student.get('student_class')
            if class_id:
                params['class_group'] = class_id
        return self.get('/lessons/', params=params)

    # --- Grades ---
    def get_grades(self, student_id):
        return self.get('/grades/', params={'student': student_id})

    def create_grade(self, student_id, subject_id, grade, date, teacher_id=None):
        data = {
            'student': student_id,
            'subject': subject_id,
            'grade': grade,
            'date': date,
        }
        if teacher_id:
            # Бот всегда ходит в API под служебной учётной записью (см. __init__),
            # поэтому реальный автор оценки передаётся отдельным полем — иначе
            # оценка была бы записана от имени этой служебной учётки.
            data['acting_teacher_id'] = teacher_id
        return self.post('/grades/', data=data)

    # --- Substitutions ---
    def get_substitutions(self, status=None):
        params = {}
        if status:
            params['status'] = status
        return self.get('/substitutions/', params=params)

    def create_substitution(self, lesson_id, new_teacher_id, reason, initiator_id):
        return self.post('/substitutions/', data={
            'original_lesson': lesson_id,
            'new_teacher': new_teacher_id,
            'reason': reason,
            'acting_initiator_id': initiator_id,
        })

    def confirm_substitution(self, sub_id):
        return self.patch(f'/substitutions/{sub_id}/confirm/')

    def reject_substitution(self, sub_id):
        return self.patch(f'/substitutions/{sub_id}/reject/')

    # --- Reports ---
    def get_workload_report(self):
        return self.get('/reports/workload/')

    def get_grade_statistics(self):
        return self.get('/reports/grades/')

    def get_attendance_report(self):
        return self.get('/reports/attendance/')
