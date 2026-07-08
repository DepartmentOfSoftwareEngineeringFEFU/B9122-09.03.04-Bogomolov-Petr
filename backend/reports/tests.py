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

        self.cls2 = Class.objects.create(name='7Б', default_classroom='Каб. 2')
        self.student3 = User.objects.create_user(
            username='s3', password='p', full_name='Ученик 3',
            phone='+4', role='student', student_class=self.cls2,
        )
        self.subject2 = Subject.objects.create(name='Химия')
        self.lesson2 = Lesson.objects.create(
            subject=self.subject2, teacher=self.teacher,
            class_group=self.cls2, day_of_week=2,
            start_time='09:00', end_time='09:45',
        )
        Grade.objects.create(
            student=self.student1, subject=self.subject, grade=4,
            date='2026-06-01', teacher=self.teacher,
        )
        Grade.objects.create(
            student=self.student3, subject=self.subject2, grade=2,
            date='2026-06-02', teacher=self.teacher,
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

    def test_dashboard_shows_both_subjects_unfiltered(self):
        self.client.login(username='admin', password='p')
        response = self.client.get(reverse('reports_dashboard'))
        self.assertContains(response, 'Труд')
        self.assertContains(response, 'Химия')

    def test_dashboard_filter_by_subject_narrows_grade_stats(self):
        # Note: the class/subject <select> dropdowns always list every option
        # (so the admin can switch the filter), so we assert on the actual
        # aggregated data in the response context rather than raw page text.
        self.client.login(username='admin', password='p')
        response = self.client.get(reverse('reports_dashboard'), {'subject_id': self.subject.id})
        subject_names = [row['subject__name'] for row in response.context['grade_stats']]
        self.assertEqual(subject_names, ['Труд'])

    def test_dashboard_filter_by_class_narrows_workload(self):
        self.client.login(username='admin', password='p')
        response = self.client.get(reverse('reports_dashboard'), {'class_id': self.cls.id})
        # Only lesson for cls (1 занятие) counted, not lesson2 for cls2.
        self.assertEqual(response.context['total_lessons'], 1)

    def test_dashboard_no_filter_counts_all_lessons(self):
        self.client.login(username='admin', password='p')
        response = self.client.get(reverse('reports_dashboard'))
        self.assertEqual(response.context['total_lessons'], 2)

    def test_dashboard_exposes_chart_json_data(self):
        self.client.login(username='admin', password='p')
        response = self.client.get(reverse('reports_dashboard'), {'subject_id': self.subject.id})
        self.assertContains(response, 'id="grade-trend-labels"')
        self.assertContains(response, '"01.06.2026"')
        self.assertContains(response, 'id="grade-dist-values"')

    def test_dashboard_filter_dropdowns_present(self):
        self.client.login(username='admin', password='p')
        response = self.client.get(reverse('reports_dashboard'))
        self.assertContains(response, 'name="class_id"')
        self.assertContains(response, 'name="subject_id"')
        self.assertContains(response, '7Б')
