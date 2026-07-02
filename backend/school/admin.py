from django.contrib import admin

from .models import Class, ClassSubject, Subject


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'homeroom_teacher', 'default_classroom']
    search_fields = ['name']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ['class_group', 'subject', 'hours_per_week']
    list_filter = ['class_group']
    search_fields = ['class_group__name', 'subject__name']
