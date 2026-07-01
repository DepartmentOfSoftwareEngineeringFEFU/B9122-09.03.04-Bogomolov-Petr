from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from school.models import Class


class AccountsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin', password='pass123',
            full_name='Админ', phone='+0', role='admin',
        )
        self.teacher = User.objects.create_user(
            username='teacher', password='pass123',
            full_name='Учитель', phone='+1', role='teacher',
        )
        self.student = User.objects.create_user(
            username='student', password='pass123',
            full_name='Ученик', phone='+2', role='student',
        )
        self.cls = Class.objects.create(name='10А', default_classroom='Каб. 301')

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_admin_login_redirects_to_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': 'admin', 'password': 'pass123',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_teacher_login_redirects_to_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': 'teacher', 'password': 'pass123',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_student_login_redirects_to_dashboard(self):
        self.student.student_class = self.cls
        self.student.save()
        response = self.client.post(reverse('login'), {
            'username': 'student', 'password': 'pass123',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'admin', 'password': 'wrong',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверный логин или пароль')

    def test_dashboard_redirects_when_not_logged_in(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_access(self):
        self.client.login(username='admin', password='pass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/dashboard.html')

    def test_teacher_dashboard_access(self):
        self.client.login(username='teacher', password='pass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'teacher/dashboard.html')

    def test_student_dashboard_access(self):
        self.client.login(username='student', password='pass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student/dashboard.html')

    def test_admin_users_list(self):
        self.client.login(username='admin', password='pass123')
        response = self.client.get(reverse('users_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Админ')
        self.assertContains(response, 'Учитель')
        self.assertContains(response, 'Ученик')

    def test_logout_requires_post(self):
        self.client.login(username='admin', password='pass123')
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
