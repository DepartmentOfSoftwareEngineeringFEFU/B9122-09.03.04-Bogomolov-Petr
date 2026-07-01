from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GradeViewSet

router = DefaultRouter()
router.register('grades', GradeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
