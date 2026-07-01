from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Grade
from .serializers import GradeSerializer


class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.select_related('student', 'subject', 'teacher').all()
    serializer_class = GradeSerializer
    filterset_fields = ['student', 'subject', 'teacher', 'date']

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'student':
            qs = qs.filter(student=user)
        elif user.role == 'teacher':
            qs = qs.filter(teacher=user)
        return qs
