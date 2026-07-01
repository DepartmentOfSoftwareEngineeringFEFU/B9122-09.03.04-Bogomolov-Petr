from django.urls import path

from .views_web import grade_add, student_grades, teacher_grades

urlpatterns = [
    path('grades/', teacher_grades, name='teacher_grades'),
    path('grades/add/', grade_add, name='grade_add'),
    path('grades/my/', student_grades, name='student_grades'),
]
