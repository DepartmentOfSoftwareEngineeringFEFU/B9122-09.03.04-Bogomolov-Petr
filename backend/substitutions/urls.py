from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SubstitutionViewSet

router = DefaultRouter()
router.register('substitutions', SubstitutionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
