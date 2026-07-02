from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Class(models.Model):
    name = models.CharField('Название класса', max_length=10, unique=True)
    homeroom_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Классный руководитель',
        on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'teacher'},
        related_name='homeroom_classes',
    )
    default_classroom = models.CharField('Аудитория по умолчанию', max_length=50)

    class Meta:
        verbose_name = 'Класс'
        verbose_name_plural = 'Классы'
        ordering = ['name']

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField('Название дисциплины', max_length=255, unique=True)

    class Meta:
        verbose_name = 'Дисциплина'
        verbose_name_plural = 'Дисциплины'
        ordering = ['name']

    def __str__(self):
        return self.name


class ClassSubject(models.Model):
    class_group = models.ForeignKey(
        Class, verbose_name='Класс', on_delete=models.CASCADE,
        related_name='curriculum',
    )
    subject = models.ForeignKey(
        Subject, verbose_name='Дисциплина', on_delete=models.CASCADE,
    )
    hours_per_week = models.IntegerField(
        'Часов в неделю',
        validators=[MinValueValidator(1), MaxValueValidator(40)],
        default=2,
    )

    class Meta:
        verbose_name = 'Учебный план'
        verbose_name_plural = 'Учебные планы'
        unique_together = ['class_group', 'subject']
        ordering = ['class_group', 'subject']

    def __str__(self):
        return f'{self.class_group} — {self.subject} ({self.hours_per_week} ч/нед)'
