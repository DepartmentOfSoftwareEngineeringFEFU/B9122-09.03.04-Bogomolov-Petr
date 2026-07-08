from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from accounts.utils import resolve_acting_user
from .models import Substitution
from .serializers import SubstitutionSerializer
from .services import notify_substitution_created, notify_substitution_result


class SubstitutionViewSet(viewsets.ModelViewSet):
    queryset = Substitution.objects.select_related(
        'original_lesson', 'new_teacher', 'initiator',
    ).all()
    serializer_class = SubstitutionSerializer
    filterset_fields = ['status', 'initiator', 'new_teacher']

    def perform_create(self, serializer):
        initiator = resolve_acting_user(self.request, 'acting_initiator_id', role='teacher')
        sub = serializer.save(initiator=initiator)
        notify_substitution_created(sub)

    @action(detail=True, methods=['patch'])
    def confirm(self, request, pk=None):
        sub = self.get_object()
        sub.status = Substitution.Status.CONFIRMED
        sub.save(update_fields=['status'])
        notify_substitution_result(sub)
        return Response(SubstitutionSerializer(sub).data)

    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        sub = self.get_object()
        sub.status = Substitution.Status.REJECTED
        sub.save(update_fields=['status'])
        notify_substitution_result(sub)
        return Response(SubstitutionSerializer(sub).data)
