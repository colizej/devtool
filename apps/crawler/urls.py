from django.urls import path
from . import views

app_name = 'crawler'

urlpatterns = [
    path('crawler/start/<int:project_id>/', views.crawl_start, name='crawl_start'),
]
