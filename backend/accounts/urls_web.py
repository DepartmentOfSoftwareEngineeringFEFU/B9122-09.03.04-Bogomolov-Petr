from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .views_web import dashboard, user_create, user_edit, users_list

urlpatterns = [
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', dashboard, name='dashboard'),
    path('users/', users_list, name='users_list'),
    path('users/create/', user_create, name='user_create'),
    path('users/<int:pk>/edit/', user_edit, name='user_edit'),
]
