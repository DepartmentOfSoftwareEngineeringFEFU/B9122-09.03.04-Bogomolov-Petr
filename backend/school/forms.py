from django import forms

from .models import Class, Subject


class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'homeroom_teacher', 'default_classroom']
        labels = {
            'name': 'Название класса',
            'homeroom_teacher': 'Классный руководитель',
            'default_classroom': 'Аудитория по умолчанию',
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']
        labels = {'name': 'Название дисциплины'}
