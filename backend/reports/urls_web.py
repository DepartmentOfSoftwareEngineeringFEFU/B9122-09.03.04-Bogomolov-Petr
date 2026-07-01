from django.urls import path

from .views_web import reports_dashboard

urlpatterns = [
    path('reports/', reports_dashboard, name='reports_dashboard'),
]
