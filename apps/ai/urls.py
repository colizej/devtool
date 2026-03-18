from django.urls import path
from . import views

urlpatterns = [
    path('ai/fix/<int:project_id>/', views.ai_fix, name='ai_fix'),
]
