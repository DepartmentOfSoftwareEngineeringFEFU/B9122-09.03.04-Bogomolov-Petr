from django.conf import settings
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
