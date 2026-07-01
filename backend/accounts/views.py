from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import User
from .serializers import UserCreateSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    filterset_fields = ['role', 'student_class', 'is_active', 'telegram_id']
    search_fields = ['full_name', 'username', 'phone']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ('create', 'destroy', 'update', 'partial_update'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['patch'])
    def link_telegram(self, request, pk=None):
        user = self.get_object()
        telegram_id = request.data.get('telegram_id')
        if not telegram_id:
            return Response({'error': 'telegram_id required'}, status=400)
        user.telegram_id = telegram_id
        user.save(update_fields=['telegram_id'])
        return Response(UserSerializer(user).data)
