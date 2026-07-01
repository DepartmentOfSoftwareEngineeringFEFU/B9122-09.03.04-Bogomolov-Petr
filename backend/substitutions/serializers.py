from rest_framework import serializers

from .models import Substitution


class SubstitutionSerializer(serializers.ModelSerializer):
    original_lesson_info = serializers.SerializerMethodField()
    new_teacher_name = serializers.CharField(source='new_teacher.full_name', read_only=True)
    initiator_name = serializers.CharField(source='initiator.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Substitution
        fields = [
            'id', 'original_lesson', 'original_lesson_info',
            'new_teacher', 'new_teacher_name',
            'initiator', 'initiator_name',
            'reason', 'request_date', 'status', 'status_display',
        ]
        read_only_fields = ['id', 'request_date', 'initiator']

    def get_original_lesson_info(self, obj):
        lesson = obj.original_lesson
        return {
            'subject': lesson.subject.name,
            'teacher': lesson.teacher.full_name,
            'class': lesson.class_group.name,
            'day': lesson.get_day_of_week_display(),
            'time': f'{lesson.start_time}-{lesson.end_time}',
        }
