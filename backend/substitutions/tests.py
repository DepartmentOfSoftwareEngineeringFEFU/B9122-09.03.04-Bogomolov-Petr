from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from school.models import Class, Subject
from schedule.models import Lesson
from substitutions.models import Substitution


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
