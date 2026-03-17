from django.urls import path
from . import views

app_name = 'integrations'

urlpatterns = [
    path('integrations/google/auth/<int:project_id>/', views.google_auth, name='google_auth'),
    path('integrations/google/callback/', views.google_callback, name='google_callback'),
    path('integrations/gsc/import/<int:project_id>/', views.gsc_import_now, name='gsc_import_now'),
    path('integrations/seo/analyze/<int:project_id>/', views.run_seo_analysis, name='run_seo_analysis'),
    path('integrations/seo/issue/<int:issue_id>/status/', views.update_issue_status, name='update_issue_status'),
    path('integrations/ga4/import/<int:project_id>/', views.ga4_import_now, name='ga4_import_now'),
]
