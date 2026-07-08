from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from school.models import Subject
from .models import User


class UserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'full_name', 'phone', 'role', 'student_class', 'max_hours_per_week', 'subjects']
        widgets = {'subjects': forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student_class'].required = False
        self.fields['phone'].required = True
        self.fields['subjects'].required = False
        self.fields['subjects'].queryset = Subject.objects.all()


class UserEditForm(UserChangeForm):
    password = None

    class Meta(UserChangeForm.Meta):
        model = User
        fields = [
            'username', 'full_name', 'phone', 'role', 'student_class',
            'telegram_id', 'max_hours_per_week', 'subjects', 'is_active',
        ]
        widgets = {'subjects': forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student_class'].required = False
        self.fields['subjects'].required = False
        self.fields['subjects'].queryset = Subject.objects.all()


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'phone', 'telegram_id']
