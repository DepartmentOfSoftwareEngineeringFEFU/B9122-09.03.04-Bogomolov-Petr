from django.contrib import admin

from .models import Substitution


@admin.register(Substitution)
class SubstitutionAdmin(admin.ModelAdmin):
    list_display = ['original_lesson', 'new_teacher', 'initiator', 'status', 'request_date']
    list_filter = ['status']
    search_fields = ['original_lesson__subject__name', 'initiator__full_name']
