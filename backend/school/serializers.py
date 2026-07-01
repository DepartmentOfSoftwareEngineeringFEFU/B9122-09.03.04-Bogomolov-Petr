from rest_framework import serializers

from .models import Class, Subject


class ClassSerializer(serializers.ModelSerializer):
    homeroom_teacher_name = serializers.CharField(
        source='homeroom_teacher.full_name', read_only=True, default=None,
    )
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = [
            'id', 'name', 'homeroom_teacher', 'homeroom_teacher_name',
            'default_classroom', 'student_count',
        ]

    def get_student_count(self, obj):
        return obj.students.count()


class SubjectSerializer(serializers.ModelSerializer):
    lesson_count = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ['id', 'name', 'lesson_count']

    def get_lesson_count(self, obj):
        return obj.lesson_set.count()
