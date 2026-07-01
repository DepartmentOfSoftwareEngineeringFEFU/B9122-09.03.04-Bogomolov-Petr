from rest_framework import serializers

from .models import Grade


class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    student_class_name = serializers.CharField(source='student.student_class.name', read_only=True, default=None)

    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'student_name', 'student_class_name',
            'subject', 'subject_name', 'grade', 'date',
            'teacher', 'teacher_name',
        ]
        read_only_fields = ['id', 'teacher']

    def validate_grade(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Оценка должна быть от 1 до 5')
        return value
