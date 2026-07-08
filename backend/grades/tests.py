from datetime import date

from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from grades.models import Attendance, Grade
from school.models import Class, Subject
from schedule.models import Lesson


class GradesViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='teacher', password='pass123',
            full_name='Учитель', phone='+0', role='teacher',
        )
        self.student = User.objects.create_user(
            username='student', password='pass123',
            full_name='Ученик', phone='+1', role='student',
        )
        self.subject = Subject.objects.create(name='Физика')

    def test_teacher_grades_access(self):
        self.client.login(username='teacher', password='pass123')
        response = self.client.get(reverse('teacher_grades'))
        self.assertEqual(response.status_code, 200)

    def test_teacher_grades_forbidden_for_student(self):
        self.client.login(username='student', password='pass123')
        response = self.client.get(reverse('teacher_grades'))
        self.assertEqual(response.status_code, 302)

    def test_grade_add_get(self):
        self.client.login(username='teacher', password='pass123')
        response = self.client.get(reverse('grade_add'))
        self.assertEqual(response.status_code, 200)

    def test_grade_add_post(self):
        self.client.login(username='teacher', password='pass123')
        response = self.client.post(reverse('grade_add'), {
            'student': self.student.id,
            'subject': self.subject.id,
            'grade': 4,
            'date': '2026-06-01',
        })
        self.assertRedirects(response, reverse('teacher_grades'))
        self.assertEqual(Grade.objects.count(), 1)
        grade = Grade.objects.first()
        self.assertEqual(grade.grade, 4)
        self.assertEqual(grade.student, self.student)
        self.assertEqual(grade.teacher, self.teacher)
        self.assertEqual(str(grade.date), '2026-06-01')

    def test_grade_add_defaults_today(self):
        self.client.login(username='teacher', password='pass123')
        response = self.client.post(reverse('grade_add'), {
            'student': self.student.id,
            'subject': self.subject.id,
            'grade': 5,
        })
        self.assertRedirects(response, reverse('teacher_grades'))
        grade = Grade.objects.first()
        self.assertEqual(grade.grade, 5)
        self.assertEqual(grade.date, date.today())

    def test_student_grades_access(self):
        self.client.login(username='student', password='pass123')
        response = self.client.get(reverse('student_grades'))
        self.assertEqual(response.status_code, 200)

    def test_student_grades_shows_avg(self):
        Grade.objects.bulk_create([
            Grade(student=self.student, subject=self.subject,
                  grade=4, date='2026-06-01', teacher=self.teacher),
            Grade(student=self.student, subject=self.subject,
                  grade=5, date='2026-06-02', teacher=self.teacher),
        ])
        self.client.login(username='student', password='pass123')
        response = self.client.get(reverse('student_grades'))
        self.assertContains(response, 'Средний балл')

    def test_student_grades_forbidden_for_teacher(self):
        self.client.login(username='teacher', password='pass123')
        response = self.client.get(reverse('student_grades'))
        self.assertEqual(response.status_code, 302)


class GradesApiTest(TestCase):
    """API_03/FR_T3: оценка, выставленная через сервисный (staff) API-аккаунт
    бота от имени конкретного учителя, должна быть записана именно за ним,
    а не за служебной учётной записью бота."""

    def setUp(self):
        self.client = Client()
        self.bot_service_account = User.objects.create_user(
            username='botsvc', password='pass123', full_name='Bot Service',
            phone='+9', role='admin', is_staff=True,
        )
        self.teacher1 = User.objects.create_user(
            username='t1', password='pass123', full_name='Учитель Один',
            phone='+1', role='teacher',
        )
        self.teacher2 = User.objects.create_user(
            username='t2', password='pass123', full_name='Учитель Два',
            phone='+2', role='teacher',
        )
        self.student = User.objects.create_user(
            username='stu', password='pass123', full_name='Ученик',
            phone='+3', role='student',
        )
        self.subject = Subject.objects.create(name='Биология')

    def test_staff_can_create_grade_on_behalf_of_teacher(self):
        self.client.login(username='botsvc', password='pass123')
        response = self.client.post('/api/grades/', {
            'student': self.student.id,
            'subject': self.subject.id,
            'grade': 5,
            'date': '2026-06-01',
            'acting_teacher_id': self.teacher1.id,
        })
        self.assertEqual(response.status_code, 201)
        grade = Grade.objects.get()
        self.assertEqual(grade.teacher, self.teacher1)

    def test_non_staff_cannot_impersonate_teacher(self):
        self.client.login(username='t1', password='pass123')
        response = self.client.post('/api/grades/', {
            'student': self.student.id,
            'subject': self.subject.id,
            'grade': 5,
            'date': '2026-06-01',
            'acting_teacher_id': self.teacher2.id,
        })
        self.assertEqual(response.status_code, 201)
        grade = Grade.objects.get()
        self.assertEqual(grade.teacher, self.teacher1)


class AttendanceTest(TestCase):
    """FR_A5/UI_06: учёт посещаемости."""

    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='teacher', password='pass123', full_name='Учитель',
            phone='+0', role='teacher',
        )
        self.other_teacher = User.objects.create_user(
            username='other', password='pass123', full_name='Другой учитель',
            phone='+9', role='teacher',
        )
        self.cls = Class.objects.create(name='5А', default_classroom='Каб. 12')
        self.student1 = User.objects.create_user(
            username='s1', password='pass123', full_name='Ученик 1',
            phone='+1', role='student', student_class=self.cls,
        )
        self.student2 = User.objects.create_user(
            username='s2', password='pass123', full_name='Ученик 2',
            phone='+2', role='student', student_class=self.cls,
        )
        self.subject = Subject.objects.create(name='ОБЖ')
        self.lesson = Lesson.objects.create(
            subject=self.subject, teacher=self.teacher,
            class_group=self.cls, day_of_week=1,
            start_time='08:00', end_time='08:45',
        )

    def test_model_unique_per_lesson_student_date(self):
        Attendance.objects.create(
            lesson=self.lesson, student=self.student1, date='2026-06-01',
            present=True, marked_by=self.teacher,
        )
        with self.assertRaises(Exception):
            Attendance.objects.create(
                lesson=self.lesson, student=self.student1, date='2026-06-01',
                present=False, marked_by=self.teacher,
            )

    def test_lesson_attendance_get_shows_students(self):
        self.client.login(username='teacher', password='pass123')
        response = self.client.get(reverse('lesson_attendance', args=[self.lesson.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ученик 1')
        self.assertContains(response, 'Ученик 2')

    def test_lesson_attendance_forbidden_for_other_teacher(self):
        self.client.login(username='other', password='pass123')
        response = self.client.get(reverse('lesson_attendance', args=[self.lesson.id]))
        self.assertEqual(response.status_code, 404)

    def test_lesson_attendance_post_marks_present_and_absent(self):
        self.client.login(username='teacher', password='pass123')
        response = self.client.post(reverse('lesson_attendance', args=[self.lesson.id]), {
            f'present_{self.student1.id}': 'on',
            # student2 checkbox omitted -> absent
        })
        self.assertRedirects(response, reverse('lesson_attendance', args=[self.lesson.id]))
        a1 = Attendance.objects.get(student=self.student1)
        a2 = Attendance.objects.get(student=self.student2)
        self.assertTrue(a1.present)
        self.assertFalse(a2.present)
        self.assertEqual(a1.marked_by, self.teacher)

    def test_lesson_attendance_post_updates_existing(self):
        Attendance.objects.create(
            lesson=self.lesson, student=self.student1, date=date.today(),
            present=False, marked_by=self.teacher,
        )
        self.client.login(username='teacher', password='pass123')
        self.client.post(reverse('lesson_attendance', args=[self.lesson.id]), {
            f'present_{self.student1.id}': 'on',
        })
        self.assertEqual(Attendance.objects.filter(student=self.student1).count(), 1)
        self.assertTrue(Attendance.objects.get(student=self.student1).present)


class AttendanceApiTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.bot_service_account = User.objects.create_user(
            username='botsvc', password='p', full_name='Bot Service',
            phone='+9', role='admin', is_staff=True,
        )
        self.teacher = User.objects.create_user(
            username='t1', password='p', full_name='Учитель',
            phone='+1', role='teacher',
        )
        self.cls = Class.objects.create(name='4Б', default_classroom='Каб. 8')
        self.student = User.objects.create_user(
            username='stu', password='p', full_name='Ученик',
            phone='+2', role='student', student_class=self.cls,
        )
        self.subject = Subject.objects.create(name='Музыка')
        self.lesson = Lesson.objects.create(
            subject=self.subject, teacher=self.teacher,
            class_group=self.cls, day_of_week=2,
            start_time='09:00', end_time='09:45',
        )

    def test_staff_can_mark_attendance_on_behalf_of_teacher(self):
        self.client.login(username='botsvc', password='p')
        response = self.client.post('/api/attendance/', {
            'lesson': self.lesson.id,
            'student': self.student.id,
            'date': '2026-06-01',
            'present': True,
            'acting_teacher_id': self.teacher.id,
        })
        self.assertEqual(response.status_code, 201)
        record = Attendance.objects.get()
        self.assertEqual(record.marked_by, self.teacher)

    def test_student_sees_only_own_attendance(self):
        other_student = User.objects.create_user(
            username='stu2', password='p', full_name='Другой ученик',
            phone='+3', role='student', student_class=self.cls,
        )
        Attendance.objects.create(
            lesson=self.lesson, student=self.student, date='2026-06-01',
            present=True, marked_by=self.teacher,
        )
        Attendance.objects.create(
            lesson=self.lesson, student=other_student, date='2026-06-01',
            present=False, marked_by=self.teacher,
        )
        self.client.login(username='stu', password='p')
        response = self.client.get('/api/attendance/')
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['student'], self.student.id)
