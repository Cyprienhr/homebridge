from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('<int:pk>/', views.report_detail, name='report_detail'),
    path('create/', views.report_create, name='report_create'),
    path('report-abandoned-child/', views.report_abandoned_child, name='report_abandoned_child'),
    path('<int:pk>/update/', views.report_update, name='report_update'),
    path('<int:pk>/delete/', views.report_delete, name='report_delete'),
    path('<int:report_id>/review-adoption/', views.review_child_adoption, name='review_child_adoption'),
]
