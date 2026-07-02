import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from accounts.models import User
from school.models import Class, ClassSubject, Subject
from schedule.models import Lesson
from grades.models import Grade
from substitutions.models import Substitution


def seed():
    print('Создание тестовых данных...')

    admin, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'full_name': 'Иванов Иван Иванович',
            'phone': '+7(999)111-22-33',
            'role': 'admin',
            'password': make_password('admin'),
            'is_staff': True,
            'is_superuser': True,
        },
    )

    teacher1, _ = User.objects.get_or_create(
        username='ivanova',
        defaults={
            'full_name': 'Иванова Мария Петровна',
            'phone': '+7(999)111-22-34',
            'role': 'teacher',
            'max_hours_per_week': 24,
            'password': make_password('teacher1'),
        },
    )

    teacher2, _ = User.objects.get_or_create(
        username='petrov',
        defaults={
            'full_name': 'Петров Сергей Владимирович',
            'phone': '+7(999)111-22-35',
            'role': 'teacher',
            'max_hours_per_week': 24,
            'password': make_password('teacher2'),
        },
    )

    class_a, _ = Class.objects.get_or_create(
        name='10А',
        defaults={
            'homeroom_teacher': teacher1,
            'default_classroom': 'Каб. 301',
        },
    )

    class_b, _ = Class.objects.get_or_create(
        name='10Б',
        defaults={
            'homeroom_teacher': teacher2,
            'default_classroom': 'Каб. 302',
        },
    )

    subjects_data = ['Математика', 'Физика', 'Информатика', 'Русский язык', 'Литература', 'Английский язык', 'История']
    subjects = {}
    for name in subjects_data:
        subj, _ = Subject.objects.get_or_create(name=name)
        subjects[name] = subj

    students_data = [
        ('Алексеев Дмитрий', class_a, 'alekseev'),
        ('Белова Анна', class_a, 'belova'),
        ('Васильев Иван', class_a, 'vasilev'),
        ('Григорьев Максим', class_b, 'grigorev'),
        ('Дмитриева Ольга', class_b, 'dmitrieva'),
        ('Егоров Артём', class_b, 'egorov'),
    ]
    students = []
    for full_name, cls, login in students_data:
        student, _ = User.objects.get_or_create(
            username=login,
            defaults={
                'full_name': full_name,
                'phone': f'+7(999)000-00-0{len(students) + 1}',
                'role': 'student',
                'student_class': cls,
                'password': make_password('student'),
            },
        )
        students.append(student)

    curriculum_data = [
        (class_a, subjects['Математика'], 2),
        (class_a, subjects['Физика'], 2),
        (class_a, subjects['Информатика'], 1),
        (class_a, subjects['Английский язык'], 1),
        (class_b, subjects['Русский язык'], 1),
        (class_b, subjects['Литература'], 1),
        (class_b, subjects['Информатика'], 1),
        (class_b, subjects['История'], 1),
        (class_b, subjects['Математика'], 1),
    ]
    for cls, subj, hours in curriculum_data:
        ClassSubject.objects.get_or_create(
            class_group=cls, subject=subj,
            defaults={'hours_per_week': hours},
        )

    lessons_data = [
        (subjects['Математика'], teacher1, class_a, 1, '08:00', '08:45', 'лекция'),
        (subjects['Математика'], teacher1, class_a, 1, '08:55', '09:40', 'практика'),
        (subjects['Физика'], teacher2, class_a, 1, '09:50', '10:35', 'лекция'),
        (subjects['Информатика'], teacher2, class_b, 1, '08:00', '08:45', 'лекция'),
        (subjects['Русский язык'], teacher1, class_b, 2, '08:00', '08:45', 'практика'),
        (subjects['Литература'], teacher1, class_b, 2, '08:55', '09:40', 'лекция'),
        (subjects['Английский язык'], teacher2, class_a, 2, '09:50', '10:35', 'практика'),
        (subjects['История'], teacher2, class_b, 3, '08:00', '08:45', 'лекция'),
        (subjects['Математика'], teacher1, class_b, 3, '08:55', '09:40', 'лекция'),
        (subjects['Физика'], teacher2, class_a, 4, '08:00', '08:45', 'практика'),
    ]
    lessons = []
    for subj, teacher, cls, day, start, end, ltype in lessons_data:
        lesson, _ = Lesson.objects.get_or_create(
            subject=subj, teacher=teacher, class_group=cls,
            day_of_week=day, start_time=start, end_time=end,
            defaults={'lesson_type': ltype},
        )
        lessons.append(lesson)

    grades_data = [
        (students[0], subjects['Математика'], 4, '2026-05-20', teacher1),
        (students[0], subjects['Физика'], 5, '2026-05-21', teacher2),
        (students[1], subjects['Математика'], 3, '2026-05-20', teacher1),
        (students[1], subjects['Физика'], 4, '2026-05-21', teacher2),
        (students[2], subjects['Математика'], 5, '2026-05-20', teacher1),
        (students[2], subjects['Информатика'], 5, '2026-05-22', teacher2),
    ]
    for student, subj, grade, date, teacher in grades_data:
        Grade.objects.get_or_create(
            student=student, subject=subj, date=date, teacher=teacher,
            defaults={'grade': grade},
        )

    substitution, _ = Substitution.objects.get_or_create(
        original_lesson=lessons[0],
        defaults={
            'new_teacher': teacher2,
            'initiator': teacher1,
            'reason': 'Участие в конференции',
            'status': 'pending',
        },
    )

    print('Готово!')
    print(f'  Администратор: {admin.username} / admin')
    print(f'  Преподаватели: {teacher1.username} / teacher1, {teacher2.username} / teacher2')
    print(f'  Учащиеся: {", ".join(s.full_name for s in students)} / student')
    print(f'  Классы: {class_a.name}, {class_b.name}')
    print(f'  Дисциплин: {Subject.objects.count()}')
    print(f'  Занятий: {Lesson.objects.count()}')
    print(f'  Оценок: {Grade.objects.count()}')
    print(f'  Замен: {Substitution.objects.count()}')


if __name__ == '__main__':
    seed()
