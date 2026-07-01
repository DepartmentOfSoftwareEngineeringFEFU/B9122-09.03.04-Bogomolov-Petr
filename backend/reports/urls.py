from django.urls import path

from .views import grade_statistics, schedule_summary, workload_report

urlpatterns = [
    path('reports/workload/', workload_report, name='workload-report'),
    path('reports/grades/', grade_statistics, name='grade-statistics'),
    path('reports/schedule/', schedule_summary, name='schedule-summary'),
]
