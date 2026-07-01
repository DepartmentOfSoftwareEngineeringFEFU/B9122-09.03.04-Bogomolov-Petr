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
