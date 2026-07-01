from django.contrib import admin

from .models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'grade', 'date', 'teacher']
    list_filter = ['subject', 'date']
    search_fields = ['student__full_name', 'subject__name']
