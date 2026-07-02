from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        TEACHER = 'teacher', 'Преподаватель'
        STUDENT = 'student', 'Учащийся'

    username = models.CharField('Логин', max_length=150, unique=True)
    first_name = None
    last_name = None
    full_name = models.CharField('ФИО', max_length=255)
    phone = models.CharField('Телефон', max_length=20)
    role = models.CharField('Роль', max_length=10, choices=Role.choices, default=Role.STUDENT)
    max_hours_per_week = models.IntegerField(
        'Макс. часов в неделю', null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(80)],
        help_text='Максимальная недельная нагрузка (только для преподавателей)',
    )
    telegram_id = models.BigIntegerField('Telegram ID', null=True, blank=True, unique=True)
    student_class = models.ForeignKey(
        'school.Class', verbose_name='Класс', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='students',
    )
    email = models.EmailField(blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['full_name', 'role']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.full_name} ({self.get_role_display()})'
