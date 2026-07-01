from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path

from accounts.views_web import dashboard, profile_edit, user_create, user_edit, users_list
from grades.views_web import grade_add, lesson_grade, student_grades, teacher_grades
from reports.views_web import reports_dashboard
from schedule.views_web import (my_schedule, schedule_add, schedule_generate,
                                schedule_list, schedule_move)
from school.views_web import (classes_list, class_create, class_edit,
                               subject_create, subject_delete, subject_edit,
                               subjects_list)
from substitutions.views_web import (substitution_confirm, substitution_reject,
                                      substitution_request, substitutions_list)

urlpatterns = [
    path('api/', include('accounts.urls')),
    path('api/', include('school.urls')),
    path('api/', include('schedule.urls')),
    path('api/', include('substitutions.urls')),
    path('api/', include('grades.urls')),
    path('api/', include('reports.urls')),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', dashboard, name='dashboard'),
    path('admin/users/', users_list, name='users_list'),
    path('admin/users/create/', user_create, name='user_create'),
    path('admin/users/<int:pk>/edit/', user_edit, name='user_edit'),
    path('admin/classes/', include('school.urls_web')),
    path('admin/schedule/', schedule_list, name='schedule_list'),
    path('admin/schedule/add/', schedule_add, name='schedule_add'),
    path('admin/schedule/generate/', schedule_generate, name='schedule_generate'),
    path('admin/schedule/move/', schedule_move, name='schedule_move'),
    path('admin/substitutions/', substitutions_list, name='substitutions_list'),
    path('admin/substitutions/<int:pk>/confirm/', substitution_confirm, name='substitution_confirm'),
    path('admin/substitutions/<int:pk>/reject/', substitution_reject, name='substitution_reject'),
    path('admin/reports/', reports_dashboard, name='reports_dashboard'),
    path('teacher/substitution/request/', substitution_request, name='substitution_request'),
    path('teacher/schedule/', my_schedule, name='teacher_schedule'),
    path('teacher/grades/', teacher_grades, name='teacher_grades'),
    path('teacher/grades/add/', grade_add, name='grade_add'),
    path('teacher/lessons/<int:lesson_id>/grade/', lesson_grade, name='lesson_grade'),
    path('student/schedule/', my_schedule, name='student_schedule'),
    path('student/grades/', student_grades, name='student_grades'),
    path('profile/', profile_edit, name='profile'),
    path('admin/', admin.site.urls),
]
