from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClassSubjectViewSet, ClassViewSet, SubjectViewSet

router = DefaultRouter()
router.register('classes', ClassViewSet)
router.register('subjects', SubjectViewSet)
router.register('class-subjects', ClassSubjectViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
