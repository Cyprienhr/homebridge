from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('logs/', views.audit_log_list, name='audit_log_list'),
    path('trash/', views.AuditLogListView.as_view(), name='audit_trash'),
]
