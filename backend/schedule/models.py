from django.conf import settings
from django.db import models


class Lesson(models.Model):
    class LessonType(models.TextChoices):
        LECTURE = 'лекция', 'Лекция'
        PRACTICE = 'практика', 'Практика'
        LAB = 'лабораторная работа', 'Лабораторная работа'
        SEMINAR = 'семинар', 'Семинар'

    DAY_CHOICES = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
    ]

    subject = models.ForeignKey('school.Subject', verbose_name='Дисциплина', on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Преподаватель',
        limit_choices_to={'role': 'teacher'},
        on_delete=models.CASCADE, related_name='lessons_taught',
    )
    class_group = models.ForeignKey(
        'school.Class', verbose_name='Класс',
        on_delete=models.CASCADE, related_name='lessons',
    )
    day_of_week = models.IntegerField('День недели', choices=DAY_CHOICES)
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    lesson_type = models.CharField('Тип занятия', max_length=50, choices=LessonType.choices, default=LessonType.LECTURE)

    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f'{self.subject.name} — {self.class_group.name} ({self.get_day_of_week_display()}, {self.start_time})'
