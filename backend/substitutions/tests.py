from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from school.models import Class, Subject
from schedule.models import Lesson
from substitutions.models import Substitution
from substitutions.services import notify_substitution_created, notify_substitution_result


class SubstitutionsModelsTest(TestCase):
    def setUp(self):
        self.teacher1 = User.objects.create_user(
            username='t1', password='pass123',
            full_name='Учитель 1', phone='+0', role='teacher',
        )
        self.teacher2 = User.objects.create_user(
            username='t2', password='pass123',
            full_name='Учитель 2', phone='+1', role='teacher',
        )
        self.admin = User.objects.create_user(
            username='admin', password='pass123',
            full_name='Админ', phone='+2', role='admin',
        )
        self.cls = Class.objects.create(name='11А', default_classroom='Каб. 401')
        self.subject = Subject.objects.create(name='История')
        self.lesson = Lesson.objects.create(
            subject=self.subject, teacher=self.teacher1,
            class_group=self.cls, day_of_week=1,
            start_time='08:00', end_time='08:45',
        )

    def test_substitution_confirm(self):
        sub = Substitution.objects.create(
            original_lesson=self.lesson, new_teacher=self.teacher2,
            initiator=self.teacher1, reason='Болен',
        )
        sub.status = Substitution.Status.CONFIRMED
        sub.save()
        self.assertEqual(sub.status, 'confirmed')
        self.assertEqual(sub.get_status_display(), 'Подтверждена')

    def test_substitution_reject(self):
        sub = Substitution.objects.create(
            original_lesson=self.lesson, new_teacher=self.teacher2,
            initiator=self.teacher1, reason='Болен',
        )
        sub.status = Substitution.Status.REJECTED
        sub.save()
        self.assertEqual(sub.status, 'rejected')

    def test_substitution_status_transitions(self):
        sub = Substitution.objects.create(
            original_lesson=self.lesson, new_teacher=self.teacher2,
            initiator=self.teacher1, reason='Тест',
        )
        self.assertEqual(sub.status, 'pending')
        sub.status = 'confirmed'
        sub.save()
        self.assertEqual(sub.status, 'confirmed')
        sub.status = 'rejected'
        sub.save()
        self.assertEqual(sub.status, 'rejected')


class SubstitutionsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin', password='pass123',
            full_name='Админ', phone='+0', role='admin',
        )
        self.teacher1 = User.objects.create_user(
            username='t1', password='pass123',
            full_name='Учитель 1', phone='+1', role='teacher',
        )
        self.teacher2 = User.objects.create_user(
            username='t2', password='pass123',
            full_name='Учитель 2', phone='+2', role='teacher',
        )
        self.cls = Class.objects.create(name='9Б', default_classroom='Каб. 201')
        self.subject = Subject.objects.create(name='Алгебра')
        self.lesson = Lesson.objects.create(
            subject=self.subject, teacher=self.teacher1,
            class_group=self.cls, day_of_week=2,
            start_time='09:00', end_time='09:45',
        )

    def test_admin_substitutions_list_access(self):
        self.client.login(username='admin', password='pass123')
        response = self.client.get(reverse('substitutions_list'))
        self.assertEqual(response.status_code, 200)

    def test_teacher_substitutions_list_access(self):
        self.client.login(username='t1', password='pass123')
        response = self.client.get(reverse('substitutions_list'))
        self.assertEqual(response.status_code, 200)

    def test_substitution_request_get(self):
        self.client.login(username='t1', password='pass123')
        response = self.client.get(reverse('substitution_request'))
        self.assertEqual(response.status_code, 200)

    def test_substitution_request_post(self):
        self.client.login(username='t1', password='pass123')
        response = self.client.post(reverse('substitution_request'), {
            'lesson': self.lesson.id,
            'new_teacher': self.teacher2.id,
            'reason': 'Срочный вызов',
        })
        self.assertRedirects(response, reverse('substitutions_list'))
        self.assertEqual(Substitution.objects.count(), 1)
        sub = Substitution.objects.first()
        self.assertEqual(sub.initiator, self.teacher1)
        self.assertEqual(sub.new_teacher, self.teacher2)
        self.assertEqual(sub.reason, 'Срочный вызов')
        self.assertEqual(sub.status, 'pending')

    def test_substitution_confirm(self):
        sub = Substitution.objects.create(
            original_lesson=self.lesson, new_teacher=self.teacher2,
            initiator=self.teacher1, reason='Тест',
        )
        self.client.login(username='admin', password='pass123')
        response = self.client.get(reverse('substitution_confirm', args=[sub.pk]))
        self.assertRedirects(response, reverse('substitutions_list'))
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'confirmed')

    def test_substitution_reject(self):
        sub = Substitution.objects.create(
            original_lesson=self.lesson, new_teacher=self.teacher2,
            initiator=self.teacher1, reason='Тест',
        )
        self.client.login(username='admin', password='pass123')
        response = self.client.get(reverse('substitution_reject', args=[sub.pk]))
        self.assertRedirects(response, reverse('substitutions_list'))
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'rejected')

    def test_substitution_list_shows_pending(self):
        sub = Substitution.objects.create(
            original_lesson=self.lesson, new_teacher=self.teacher2,
            initiator=self.teacher1, reason='Тест',
        )
        self.client.login(username='admin', password='pass123')
        response = self.client.get(reverse('substitutions_list'))
        self.assertContains(response, 'Тест')

    def test_teacher_sees_own_substitutions(self):
        sub = Substitution.objects.create(
            original_lesson=self.lesson, new_teacher=self.teacher2,
            initiator=self.teacher1, reason='Моя замена',
        )
        self.client.login(username='t1', password='pass123')
        response = self.client.get(reverse('substitutions_list'))
        self.assertContains(response, 'Учитель 2')


class SubstitutionsApiTest(TestCase):
    """API_03/FR_T2: заявка на замену, созданная через сервисный (staff)
    API-аккаунт бота от имени конкретного учителя, должна быть записана
    как инициированная этим учителем, а не служебной учёткой бота."""

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
        self.cls = Class.objects.create(name='8В', default_classroom='Каб. 5')
        self.subject = Subject.objects.create(name='Геометрия')
        self.lesson = Lesson.objects.create(
            subject=self.subject, teacher=self.teacher1,
            class_group=self.cls, day_of_week=3,
            start_time='10:00', end_time='10:45',
        )

    def test_staff_can_create_substitution_on_behalf_of_teacher(self):
        self.client.login(username='botsvc', password='pass123')
        response = self.client.post('/api/substitutions/', {
            'original_lesson': self.lesson.id,
            'new_teacher': self.teacher2.id,
            'reason': 'Через бота',
            'acting_initiator_id': self.teacher1.id,
        })
        self.assertEqual(response.status_code, 201)
        sub = Substitution.objects.get()
        self.assertEqual(sub.initiator, self.teacher1)

    def test_non_staff_cannot_impersonate_initiator(self):
        self.client.login(username='t1', password='pass123')
        response = self.client.post('/api/substitutions/', {
            'original_lesson': self.lesson.id,
            'new_teacher': self.teacher2.id,
            'reason': 'Сам за себя',
            'acting_initiator_id': self.teacher2.id,
        })
        self.assertEqual(response.status_code, 201)
        sub = Substitution.objects.get()
        self.assertEqual(sub.initiator, self.teacher1)


@patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test-token'})
class SubstitutionNotificationsTest(TestCase):
    """FR_T5, FR_S3, TG_04: push-уведомления о заменах."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='p', full_name='Админ',
            phone='+0', role='admin', telegram_id=111,
        )
        self.teacher1 = User.objects.create_user(
            username='t1', password='p', full_name='Учитель Первый',
            phone='+1', role='teacher', telegram_id=222,
        )
        self.teacher2 = User.objects.create_user(
            username='t2', password='p', full_name='Учитель Второй',
            phone='+2', role='teacher', telegram_id=333,
        )
        self.cls = Class.objects.create(name='7А', default_classroom='Каб. 101')
        self.student = User.objects.create_user(
            username='s1', password='p', full_name='Ученик Первый',
            phone='+3', role='student', telegram_id=444, student_class=self.cls,
        )
        self.student_no_tg = User.objects.create_user(
            username='s2', password='p', full_name='Ученик Второй',
            phone='+4', role='student', student_class=self.cls,
        )
        self.subject = Subject.objects.create(name='Химия')
        self.lesson = Lesson.objects.create(
            subject=self.subject, teacher=self.teacher1,
            class_group=self.cls, day_of_week=1,
            start_time='08:00', end_time='08:45',
        )

    def _chat_ids(self, mock_post):
        return [call.kwargs['json']['chat_id'] for call in mock_post.call_args_list]

    @patch('accounts.notifications.requests.post')
    def test_create_notifies_admin(self, mock_post):
        mock_post.return_value.status_code = 200
        sub = Substitution.objects.create(
            original_lesson=self.lesson, new_teacher=self.teacher2,
            initiator=self.teacher1, reason='Болезнь',
        )
        notify_substitution_created(sub)
        self.assertIn(self.admin.telegram_id, self._chat_ids(mock_post))

    @patch('accounts.notifications.requests.post')
    def test_confirm_notifies_initiator_new_teacher_and_class(self, mock_post):
        mock_post.return_value.status_code = 200
        sub = Substitution.objects.create(
            original_lesson=self.lesson, new_teacher=self.teacher2,
            initiator=self.teacher1, reason='Болезнь', status='confirmed',
        )
        notify_substitution_result(sub)
        chat_ids = self._chat_ids(mock_post)
        self.assertIn(self.teacher1.telegram_id, chat_ids)
        self.assertIn(self.teacher2.telegram_id, chat_ids)
        self.assertIn(self.student.telegram_id, chat_ids)
        # Student without a linked Telegram ID must simply be skipped, not error.
        self.assertEqual(len(chat_ids), 3)

    @patch('accounts.notifications.requests.post')
    def test_reject_notifies_only_initiator(self, mock_post):
        mock_post.return_value.status_code = 200
        sub = Substitution.objects.create(
            original_lesson=self.lesson, new_teacher=self.teacher2,
            initiator=self.teacher1, reason='Болезнь', status='rejected',
        )
        notify_substitution_result(sub)
        self.assertEqual(self._chat_ids(mock_post), [self.teacher1.telegram_id])

    @patch('accounts.notifications.requests.post')
    def test_confirm_via_web_view_sends_notifications(self, mock_post):
        mock_post.return_value.status_code = 200
        sub = Substitution.objects.create(
            original_lesson=self.lesson, new_teacher=self.teacher2,
            initiator=self.teacher1, reason='Тест',
        )
        self.client.login(username='admin', password='p')
        self.client.get(reverse('substitution_confirm', args=[sub.pk]))
        chat_ids = self._chat_ids(mock_post)
        self.assertIn(self.teacher1.telegram_id, chat_ids)
        self.assertIn(self.teacher2.telegram_id, chat_ids)
