from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from grades.models import Attendance, Grade
from school.models import Class, Subject
from schedule.models import Lesson


class ReportsTestBase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin', password='p', full_name='Админ',
            phone='+0', role='admin', is_staff=True,
        )
        self.teacher = User.objects.create_user(
            username='t1', password='p', full_name='Учитель',
            phone='+1', role='teacher',
        )
        self.cls = Class.objects.create(name='6А', default_classroom='Каб. 1')
        self.student1 = User.objects.create_user(
            username='s1', password='p', full_name='Ученик 1',
            phone='+2', role='student', student_class=self.cls,
        )
        self.student2 = User.objects.create_user(
            username='s2', password='p', full_name='Ученик 2',
            phone='+3', role='student', student_class=self.cls,
        )
        self.subject = Subject.objects.create(name='Труд')
        self.lesson = Lesson.objects.create(
            subject=self.subject, teacher=self.teacher,
            class_group=self.cls, day_of_week=1,
            start_time='08:00', end_time='08:45',
        )


class AttendanceReportApiTest(ReportsTestBase):
    def test_attendance_report_computes_rate_per_class(self):
        Attendance.objects.create(
            lesson=self.lesson, student=self.student1, date='2026-06-01',
            present=True, marked_by=self.teacher,
        )
        Attendance.objects.create(
            lesson=self.lesson, student=self.student2, date='2026-06-01',
            present=False, marked_by=self.teacher,
        )
        self.client.login(username='admin', password='p')
        response = self.client.get('/api/reports/attendance/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['class_name'], '6А')
        self.assertEqual(data[0]['total'], 2)
        self.assertEqual(data[0]['present'], 1)
        self.assertEqual(data[0]['attendance_rate'], 50.0)

    def test_attendance_report_requires_admin(self):
        self.client.login(username='t1', password='p')
        response = self.client.get('/api/reports/attendance/')
        self.assertEqual(response.status_code, 403)

    def test_attendance_report_empty_without_data(self):
        self.client.login(username='admin', password='p')
        response = self.client.get('/api/reports/attendance/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


class ReportsDashboardTest(ReportsTestBase):
    def test_dashboard_shows_attendance_stats(self):
        Attendance.objects.create(
            lesson=self.lesson, student=self.student1, date='2026-06-01',
            present=True, marked_by=self.teacher,
        )
        self.client.login(username='admin', password='p')
        response = self.client.get(reverse('reports_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '6А')
        # Django-шаблоны локализуют float (запятая вместо точки при LANGUAGE_CODE='ru').
        self.assertContains(response, '100,0%')

    def test_dashboard_requires_admin(self):
        self.client.login(username='t1', password='p')
        response = self.client.get(reverse('reports_dashboard'))
        self.assertEqual(response.status_code, 302)
