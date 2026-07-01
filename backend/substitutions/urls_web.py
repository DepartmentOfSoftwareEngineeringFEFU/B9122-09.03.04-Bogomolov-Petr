from django.urls import path

from .views_web import substitutions_list, substitution_confirm, substitution_reject

urlpatterns = [
    path('substitutions/', substitutions_list, name='substitutions_list'),
    path('substitutions/<int:pk>/confirm/', substitution_confirm, name='substitution_confirm'),
    path('substitutions/<int:pk>/reject/', substitution_reject, name='substitution_reject'),
]
