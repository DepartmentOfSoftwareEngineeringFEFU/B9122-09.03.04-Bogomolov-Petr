from rest_framework import serializers

from .models import Lesson


class LessonSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    class_name = serializers.CharField(source='class_group.name', read_only=True)
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    lesson_type_display = serializers.CharField(source='get_lesson_type_display', read_only=True)
    classroom = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'subject', 'subject_name', 'teacher', 'teacher_name',
            'class_group', 'class_name', 'day_of_week', 'day_of_week_display',
            'start_time', 'end_time', 'lesson_type', 'lesson_type_display',
            'classroom',
        ]

    def get_classroom(self, obj):
        return obj.class_group.default_classroom if obj.class_group else ''
