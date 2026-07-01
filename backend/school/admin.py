from django.contrib import admin

from .models import Class, Subject


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'homeroom_teacher', 'default_classroom']
    search_fields = ['name']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
