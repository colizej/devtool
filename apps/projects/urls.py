from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('project/<slug:slug>/', views.project_detail, name='detail'),
]
