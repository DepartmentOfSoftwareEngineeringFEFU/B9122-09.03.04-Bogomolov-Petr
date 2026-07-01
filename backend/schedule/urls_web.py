from django.urls import path

from .views_web import my_schedule, schedule_add, schedule_generate, schedule_list

urlpatterns = [
    path('schedule/', schedule_list, name='schedule_list'),
    path('schedule/add/', schedule_add, name='schedule_add'),
    path('schedule/generate/', schedule_generate, name='schedule_generate'),
    path('schedule/my/', my_schedule, name='my_schedule'),
]
