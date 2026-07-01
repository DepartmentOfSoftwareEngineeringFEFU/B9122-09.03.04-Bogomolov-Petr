from django import forms

from .models import Lesson


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['subject', 'teacher', 'class_group', 'day_of_week', 'start_time', 'end_time', 'lesson_type']
        labels = {
            'subject': 'Дисциплина',
            'teacher': 'Преподаватель',
            'class_group': 'Класс',
            'day_of_week': 'День недели',
            'start_time': 'Время начала',
            'end_time': 'Время окончания',
            'lesson_type': 'Тип занятия',
        }
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'end_time': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
        }
