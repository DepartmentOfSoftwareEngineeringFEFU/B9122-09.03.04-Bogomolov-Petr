from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from .models import Lesson
from .serializers import LessonSerializer


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.select_related('subject', 'teacher', 'class_group').all()
    serializer_class = LessonSerializer
    filterset_fields = ['class_group', 'teacher', 'day_of_week', 'subject']
    search_fields = ['subject__name', 'class_group__name']

    def get_permissions(self):
        if self.action in ('create', 'destroy', 'update', 'partial_update'):
            return [IsAdminUser()]
        return [IsAuthenticated()]
