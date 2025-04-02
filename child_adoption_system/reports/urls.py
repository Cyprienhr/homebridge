from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('<int:pk>/', views.report_detail, name='report_detail'),
    path('create/', views.report_create, name='report_create'),
    path('<int:pk>/update/', views.report_update, name='report_update'),
    path('<int:pk>/delete/', views.report_delete, name='report_delete'),
]
