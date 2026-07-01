from django.test import TestCase
from django.core.exceptions import ValidationError

from accounts.models import User
from school.models import Class, Subject
from schedule.models import Lesson
from substitutions.models import Substitution
from grades.models import Grade


class UserModelTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='pass123',
            full_name='Администратор Системы', phone='+1234567890',
            role='admin',
        )
        self.teacher = User.objects.create_user(
            username='teacher1', password='pass123',
            full_name='Иванов Иван Иванович', phone='+1234567891',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='student1', password='pass123',
            full_name='Петров Пётр Петрович', phone='+1234567892',
            role='student',
        )

    def test_user_creation(self):
        self.assertEqual(User.objects.count(), 3)

    def test_user_role_admin(self):
        self.assertEqual(self.admin.role, 'admin')
        self.assertEqual(self.admin.get_role_display(), 'Администратор')

    def test_user_role_teacher(self):
        self.assertEqual(self.teacher.role, 'teacher')
        self.assertEqual(self.teacher.get_role_display(), 'Преподаватель')

    def test_user_role_student(self):
        self.assertEqual(self.student.role, 'student')
        self.assertEqual(self.student.get_role_display(), 'Учащийся')

    def test_user_str(self):
        expected = f'{self.admin.full_name} ({self.admin.get_role_display()})'
        self.assertEqual(str(self.admin), expected)

    def test_telegram_id_unique(self):
        self.admin.telegram_id = 12345
        self.admin.save()
        self.teacher.telegram_id = 12345
        with self.assertRaises(Exception):
            self.teacher.full_clean()

    def test_username_unique(self):
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='admin', password='pass',
                full_name='Дубликат', phone='+0', role='admin',
            )


class ClassModelTest(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher_cls', password='pass',
            full_name='Сидоров Сидор Сидорович',
            phone='+0', role='teacher',
        )
        self.cls = Class.objects.create(
            name='10А',
            homeroom_teacher=self.teacher,
            default_classroom='Каб. 301',
        )

    def test_class_creation(self):
        self.assertEqual(Class.objects.count(), 1)
        self.assertEqual(self.cls.name, '10А')

    def test_class_str(self):
        self.assertEqual(str(self.cls), '10А')

    def test_class_default_classroom(self):
        self.assertEqual(self.cls.default_classroom, 'Каб. 301')

    def test_class_homeroom_teacher(self):
        self.assertEqual(self.cls.homeroom_teacher, self.teacher)

    def test_class_students_relation(self):
        student = User.objects.create_user(
            username='student_cls', password='pass',
            full_name='Ученик', phone='+0', role='student',
            student_class=self.cls,
        )
        self.assertEqual(self.cls.students.count(), 1)
        self.assertIn(student, self.cls.students.all())

    def test_class_name_unique(self):
        with self.assertRaises(Exception):
            Class.objects.create(name='10А', default_classroom='Каб. 302')


class SubjectModelTest(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name='Алгебра')

    def test_subject_creation(self):
        self.assertEqual(Subject.objects.count(), 1)
        self.assertEqual(self.subject.name, 'Алгебра')

    def test_subject_str(self):
        self.assertEqual(str(self.subject), 'Алгебра')

    def test_subject_name_unique(self):
        with self.assertRaises(Exception):
            Subject.objects.create(name='Алгебра')


class LessonModelTest(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher_les', password='pass',
            full_name='Учитель', phone='+0', role='teacher',
        )
        self.cls = Class.objects.create(name='9А', default_classroom='Каб. 201')
        self.subject = Subject.objects.create(name='Физика')
        self.lesson = Lesson.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            class_group=self.cls,
            day_of_week=1,
            start_time='08:00',
            end_time='08:45',
            lesson_type='лекция',
        )

    def test_lesson_creation(self):
        self.assertEqual(Lesson.objects.count(), 1)

    def test_lesson_str(self):
        self.assertIn('Физика', str(self.lesson))
        self.assertIn('9А', str(self.lesson))

    def test_lesson_type_choices(self):
        self.assertEqual(self.lesson.lesson_type, 'лекция')

    def test_lesson_day_choices(self):
        self.assertEqual(self.lesson.day_of_week, 1)


class SubstitutionModelTest(TestCase):
    def setUp(self):
        self.teacher1 = User.objects.create_user(
            username='t1', password='pass',
            full_name='Учитель 1', phone='+0', role='teacher',
        )
        self.teacher2 = User.objects.create_user(
            username='t2', password='pass',
            full_name='Учитель 2', phone='+1', role='teacher',
        )
        self.admin = User.objects.create_user(
            username='admin_sub', password='pass',
            full_name='Админ', phone='+2', role='admin',
        )
        self.cls = Class.objects.create(name='11А', default_classroom='Каб. 401')
        self.subject = Subject.objects.create(name='История')
        self.lesson = Lesson.objects.create(
            subject=self.subject, teacher=self.teacher1,
            class_group=self.cls, day_of_week=1,
            start_time='08:00', end_time='08:45',
        )
        self.sub = Substitution.objects.create(
            original_lesson=self.lesson,
            new_teacher=self.teacher2,
            initiator=self.teacher1,
            reason='Больничный',
        )

    def test_substitution_creation(self):
        self.assertEqual(Substitution.objects.count(), 1)
        self.assertEqual(self.sub.status, 'pending')

    def test_substitution_status_choices(self):
        self.assertIn(self.sub.status, ['pending', 'confirmed', 'rejected'])

    def test_substitution_str(self):
        self.assertIn('История', str(self.sub))
        self.assertIn('Учитель 2', str(self.sub))

    def test_substitution_default_status(self):
        self.assertEqual(self.sub.get_status_display(), 'Запрошена')

    def test_substitution_same_teacher_validation(self):
        sub = Substitution(
            original_lesson=self.lesson,
            new_teacher=self.teacher1,
            initiator=self.teacher1,
            reason='Тест',
        )
        with self.assertRaises(ValidationError):
            sub.clean()


class GradeModelTest(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher_gr', password='pass',
            full_name='Учитель', phone='+0', role='teacher',
        )
        self.student = User.objects.create_user(
            username='student_gr', password='pass',
            full_name='Ученик', phone='+1', role='student',
        )
        self.subject = Subject.objects.create(name='Химия')
        self.grade = Grade.objects.create(
            student=self.student,
            subject=self.subject,
            grade=4,
            date='2026-06-01',
            teacher=self.teacher,
        )

    def test_grade_creation(self):
        self.assertEqual(Grade.objects.count(), 1)

    def test_grade_value_range(self):
        self.assertGreaterEqual(self.grade.grade, 1)
        self.assertLessEqual(self.grade.grade, 5)

    def test_grade_str(self):
        self.assertIn('Ученик', str(self.grade))
        self.assertIn('Химия', str(self.grade))
        self.assertIn('4', str(self.grade))
