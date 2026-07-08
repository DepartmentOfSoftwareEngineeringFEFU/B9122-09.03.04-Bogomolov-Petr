from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse

from accounts.forms import UserCreateForm, UserEditForm
from accounts.models import User
from accounts.notifications import notify_users, send_telegram_message
from school.models import Class, Subject


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


class TelegramLinkApiTest(TestCase):
    """Привязка/отвязка Telegram ID через API (бот использует эти эндпоинты
    от имени служебного staff-аккаунта, поэтому доступ разграничен: только
    сам пользователь или staff)."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin', password='p', full_name='Админ',
            phone='+0', role='admin', is_staff=True,
        )
        self.teacher = User.objects.create_user(
            username='t1', password='p', full_name='Учитель',
            phone='+1', role='teacher', telegram_id=111,
        )
        self.other_teacher = User.objects.create_user(
            username='t2', password='p', full_name='Другой учитель',
            phone='+2', role='teacher',
        )

    def test_staff_can_link_telegram_for_any_user(self):
        self.client.login(username='admin', password='p')
        response = self.client.patch(
            f'/api/users/{self.other_teacher.id}/link_telegram/',
            {'telegram_id': 999}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.other_teacher.refresh_from_db()
        self.assertEqual(self.other_teacher.telegram_id, 999)

    def test_user_can_link_own_telegram(self):
        self.client.login(username='t2', password='p')
        response = self.client.patch(
            f'/api/users/{self.other_teacher.id}/link_telegram/',
            {'telegram_id': 888}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.other_teacher.refresh_from_db()
        self.assertEqual(self.other_teacher.telegram_id, 888)

    def test_user_cannot_link_telegram_for_another_user(self):
        self.client.login(username='t2', password='p')
        response = self.client.patch(
            f'/api/users/{self.teacher.id}/link_telegram/',
            {'telegram_id': 777}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.telegram_id, 111)

    def test_staff_can_unlink_telegram(self):
        self.client.login(username='admin', password='p')
        response = self.client.patch(f'/api/users/{self.teacher.id}/unlink_telegram/')
        self.assertEqual(response.status_code, 200)
        self.teacher.refresh_from_db()
        self.assertIsNone(self.teacher.telegram_id)

    def test_user_can_unlink_own_telegram(self):
        self.client.login(username='t1', password='p')
        response = self.client.patch(f'/api/users/{self.teacher.id}/unlink_telegram/')
        self.assertEqual(response.status_code, 200)
        self.teacher.refresh_from_db()
        self.assertIsNone(self.teacher.telegram_id)

    def test_user_cannot_unlink_another_users_telegram(self):
        self.client.login(username='t2', password='p')
        response = self.client.patch(f'/api/users/{self.teacher.id}/unlink_telegram/')
        self.assertEqual(response.status_code, 403)
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.telegram_id, 111)


class UserFormRoleFieldsTest(TestCase):
    """Ролевые поля пользователя: у преподавателя есть предметы и норма
    часов, у учащегося — класс; форма редактирования не требует пароль."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin', password='p', full_name='Админ',
            phone='+0', role='admin', is_staff=True, is_superuser=True,
        )
        self.teacher = User.objects.create_user(
            username='t1', password='p', full_name='Учитель',
            phone='+1', role='teacher',
        )
        self.cls = Class.objects.create(name='9А', default_classroom='Каб. 1')
        self.math = Subject.objects.create(name='Математика')
        self.physics = Subject.objects.create(name='Физика')

    def test_edit_form_has_no_password_fields(self):
        form = UserEditForm(instance=self.teacher)
        self.assertNotIn('password1', form.fields)
        self.assertNotIn('password2', form.fields)
        self.assertNotIn('password', form.fields)

    def test_edit_form_includes_subjects_field(self):
        form = UserEditForm(instance=self.teacher)
        self.assertIn('subjects', form.fields)
        self.assertFalse(form.fields['subjects'].required)

    def test_create_form_includes_subjects_field(self):
        form = UserCreateForm()
        self.assertIn('subjects', form.fields)
        self.assertFalse(form.fields['subjects'].required)

    def test_user_edit_view_uses_edit_form_not_create_form(self):
        self.client.login(username='admin', password='p')
        response = self.client.get(reverse('user_edit', args=[self.teacher.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id_password1')
        self.assertNotContains(response, 'id_password2')

    def test_user_edit_form_renders_role_conditional_data_attributes(self):
        self.client.login(username='admin', password='p')
        response = self.client.get(reverse('user_edit', args=[self.teacher.id]))
        self.assertContains(response, 'data-role-fields="teacher"')
        self.assertContains(response, 'data-role-fields="student"')

    def test_saving_subjects_via_edit_view_persists_them(self):
        self.client.login(username='admin', password='p')
        response = self.client.post(reverse('user_edit', args=[self.teacher.id]), {
            'username': self.teacher.username,
            'full_name': self.teacher.full_name,
            'phone': self.teacher.phone,
            'role': 'teacher',
            'max_hours_per_week': 30,
            'subjects': [self.math.id, self.physics.id],
            'is_active': 'on',
        })
        self.assertRedirects(response, reverse('users_list'))
        self.teacher.refresh_from_db()
        self.assertEqual(
            set(self.teacher.subjects.values_list('id', flat=True)),
            {self.math.id, self.physics.id},
        )

    def test_saving_via_create_view_persists_subjects(self):
        self.client.login(username='admin', password='p')
        response = self.client.post(reverse('user_create'), {
            'username': 'newteacher',
            'full_name': 'Новый Учитель',
            'phone': '+7(999)555-55-55',
            'role': 'teacher',
            'max_hours_per_week': 20,
            'subjects': [self.math.id],
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertRedirects(response, reverse('users_list'))
        created = User.objects.get(username='newteacher')
        self.assertEqual(list(created.subjects.values_list('id', flat=True)), [self.math.id])
