from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.utils import resolve_acting_user
from .models import Attendance, Grade
from .serializers import AttendanceSerializer, GradeSerializer


class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.select_related('student', 'subject', 'teacher').all()
    serializer_class = GradeSerializer
    filterset_fields = ['student', 'subject', 'teacher', 'date']

    def perform_create(self, serializer):
        teacher = resolve_acting_user(self.request, 'acting_teacher_id', role='teacher')
        serializer.save(teacher=teacher)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'student':
            qs = qs.filter(student=user)
        elif user.role == 'teacher':
            qs = qs.filter(teacher=user)
        return qs


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related('lesson', 'student', 'marked_by').all()
    serializer_class = AttendanceSerializer
    filterset_fields = ['student', 'lesson', 'date', 'present']

    def perform_create(self, serializer):
        marker = resolve_acting_user(self.request, 'acting_teacher_id', role='teacher')
        serializer.save(marked_by=marker)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'student':
            qs = qs.filter(student=user)
        elif user.role == 'teacher':
            qs = qs.filter(lesson__teacher=user)
        return qs
