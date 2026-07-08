from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AttendanceViewSet, GradeViewSet

router = DefaultRouter()
router.register('grades', GradeViewSet)
router.register('attendance', AttendanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
