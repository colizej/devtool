from django.urls import path
from . import views

app_name = 'crawler'

urlpatterns = [
    path('crawler/start/<int:project_id>/', views.crawl_start, name='crawl_start'),
    path('crawler/reset/<int:session_id>/', views.crawl_reset, name='crawl_reset'),
    path('crawler/status/<int:session_id>/', views.crawl_status, name='crawl_status'),
]
