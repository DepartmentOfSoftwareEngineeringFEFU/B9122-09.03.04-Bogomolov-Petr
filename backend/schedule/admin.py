from django.contrib import admin

from .models import Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['subject', 'teacher', 'class_group', 'day_of_week', 'start_time', 'end_time', 'get_classroom']

    @admin.display(description='Аудитория')
    def get_classroom(self, obj):
        return obj.class_group.default_classroom if obj.class_group else ''
    list_filter = ['day_of_week', 'class_group', 'teacher']
    search_fields = ['subject__name', 'class_group__name']
