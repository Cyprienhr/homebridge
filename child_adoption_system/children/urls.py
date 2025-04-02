from django.urls import path
from . import views

app_name = 'children'

urlpatterns = [
    # Child CRUD
    path('', views.child_list, name='child_list'),
    path('<int:pk>/', views.child_detail, name='child_detail'),
    path('create/', views.child_create, name='child_create'),
    path('<int:pk>/update/', views.child_update, name='child_update'),
    path('<int:pk>/delete/', views.child_delete, name='child_delete'),
    
    # Adoption applications
    path('<int:child_id>/apply/', views.application_create, name='apply_for_adoption'),
    path('applications/', views.application_list, name='application_list'),
    path('applications/<int:pk>/', views.application_detail, name='application_detail'),
    path('applications/<int:pk>/update-status/', views.application_update_status, name='update_application_status'),
    path('applications/<int:pk>/cancel/', views.application_cancel, name='cancel_application'),
]
