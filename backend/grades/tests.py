from datetime import date

from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from grades.models import Grade
from school.models import Class, Subject


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
