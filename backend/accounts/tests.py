from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from accounts.notifications import notify_users, send_telegram_message
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


class TelegramNotificationsTest(TestCase):
    """TG_04: базовая проверка отправки push-уведомлений."""

    def test_no_telegram_id_skips_send(self):
        self.assertFalse(send_telegram_message(None, 'test'))

    @patch.dict('os.environ', {}, clear=True)
    def test_missing_token_skips_send(self):
        self.assertFalse(send_telegram_message(123, 'test'))

    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'your_bot_token_here'})
    def test_placeholder_token_skips_send(self):
        self.assertFalse(send_telegram_message(123, 'test'))

    @patch('accounts.notifications.requests.post')
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test-token'})
    def test_successful_send(self, mock_post):
        mock_post.return_value.status_code = 200
        self.assertTrue(send_telegram_message(123, 'Привет'))
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args.kwargs['json']['chat_id'], 123)

    @patch('accounts.notifications.requests.post')
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test-token'})
    def test_network_error_is_swallowed(self, mock_post):
        import requests
        mock_post.side_effect = requests.RequestException('boom')
        self.assertFalse(send_telegram_message(123, 'Привет'))

    @patch('accounts.notifications.requests.post')
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test-token'})
    def test_notify_users_skips_those_without_telegram_id(self, mock_post):
        mock_post.return_value.status_code = 200
        with_tg = User.objects.create_user(
            username='u1', password='p', full_name='С Telegram',
            phone='+1', role='teacher', telegram_id=555,
        )
        without_tg = User.objects.create_user(
            username='u2', password='p', full_name='Без Telegram',
            phone='+2', role='teacher',
        )
        sent = notify_users([with_tg, without_tg], 'test')
        self.assertEqual(sent, 1)
        mock_post.assert_called_once()
