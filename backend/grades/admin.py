from django.contrib import admin

from .models import Attendance, Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'grade', 'date', 'teacher']
    list_filter = ['subject', 'date']
    search_fields = ['student__full_name', 'subject__name']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'date', 'present', 'marked_by']
    list_filter = ['present', 'date']
    search_fields = ['student__full_name']
