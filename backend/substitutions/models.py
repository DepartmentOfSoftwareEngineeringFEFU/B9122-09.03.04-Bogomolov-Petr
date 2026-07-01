from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Substitution(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Запрошена'
        CONFIRMED = 'confirmed', 'Подтверждена'
        REJECTED = 'rejected', 'Отменена'

    original_lesson = models.ForeignKey(
        'schedule.Lesson', verbose_name='Исходное занятие',
        on_delete=models.CASCADE, related_name='substitutions',
    )
    new_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Новый преподаватель',
        limit_choices_to={'role': 'teacher'},
        on_delete=models.CASCADE, related_name='substitutions_as_new',
    )
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Инициатор',
        on_delete=models.CASCADE, related_name='substitutions_initiated',
    )
    reason = models.TextField('Причина')
    request_date = models.DateTimeField('Дата запроса', auto_now_add=True)
    status = models.CharField('Статус', max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        verbose_name = 'Замена'
        verbose_name_plural = 'Замены'
        ordering = ['-request_date']

    def clean(self):
        if self.new_teacher_id == self.original_lesson.teacher_id:
            raise ValidationError('Новый преподаватель не должен совпадать с текущим преподавателем занятия')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Замена {self.original_lesson} → {self.new_teacher.full_name}'
