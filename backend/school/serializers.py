from rest_framework import serializers

from .models import Class, ClassSubject, Subject


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


class ClassSubjectSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_group.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = ClassSubject
        fields = ['id', 'class_group', 'class_name', 'subject', 'subject_name', 'hours_per_week']
