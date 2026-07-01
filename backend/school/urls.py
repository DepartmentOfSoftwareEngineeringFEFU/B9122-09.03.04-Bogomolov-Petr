from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClassViewSet, SubjectViewSet

router = DefaultRouter()
router.register('classes', ClassViewSet)
router.register('subjects', SubjectViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
