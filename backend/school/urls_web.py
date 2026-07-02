from django.urls import path

from .views_web import (class_create, class_edit, classes_list, curriculum_add,
                         curriculum_delete, curriculum_edit, curriculum_list,
                         subject_create, subject_delete, subject_edit,
                         subjects_list)

urlpatterns = [
    path('', classes_list, name='classes_list'),
    path('create/', class_create, name='class_create'),
    path('<int:pk>/edit/', class_edit, name='class_edit'),
    path('subjects/', subjects_list, name='subjects_list'),
    path('subjects/create/', subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', subject_edit, name='subject_edit'),
    path('subjects/<int:pk>/delete/', subject_delete, name='subject_delete'),
    path('<int:class_pk>/curriculum/', curriculum_list, name='curriculum_list'),
    path('<int:class_pk>/curriculum/add/', curriculum_add, name='curriculum_add'),
    path('curriculum/<int:pk>/edit/', curriculum_edit, name='curriculum_edit'),
    path('curriculum/<int:pk>/delete/', curriculum_delete, name='curriculum_delete'),
]
