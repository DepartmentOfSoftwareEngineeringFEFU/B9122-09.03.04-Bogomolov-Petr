from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Grade(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Учащийся',
        on_delete=models.CASCADE, related_name='grades',
    )
    subject = models.ForeignKey(
        'school.Subject', verbose_name='Дисциплина',
        on_delete=models.CASCADE, related_name='grades',
    )
    grade = models.IntegerField('Оценка', validators=[MinValueValidator(1), MaxValueValidator(5)])
    date = models.DateField('Дата')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Преподаватель',
        on_delete=models.CASCADE, related_name='grades_given',
    )

    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        ordering = ['-date', 'student']

    def __str__(self):
        return f'{self.student.full_name} — {self.subject.name}: {self.grade}'


class Attendance(models.Model):
    """Учёт посещаемости (FR_A5, UI_06): отметка присутствия учащегося на
    конкретном занятии в конкретный день."""
    lesson = models.ForeignKey(
        'schedule.Lesson', verbose_name='Занятие',
        on_delete=models.CASCADE, related_name='attendance_records',
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Учащийся',
        on_delete=models.CASCADE, related_name='attendance_records',
    )
    date = models.DateField('Дата')
    present = models.BooleanField('Присутствовал', default=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Отметил',
        on_delete=models.CASCADE, related_name='attendance_marked',
    )

    class Meta:
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'
        unique_together = ['lesson', 'student', 'date']
        ordering = ['-date', 'student']

    def __str__(self):
        status = 'присутствовал' if self.present else 'отсутствовал'
        return f'{self.student.full_name} — {self.lesson} ({self.date}): {status}'
