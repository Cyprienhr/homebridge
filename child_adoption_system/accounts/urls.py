from atexit import register
from django.urls import path
from . import views
from .views import register,user_login

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('initialize-admin/', views.initialize_admin, name='initialize_admin'),
    
    # Profile management
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Local leader management
    path('local-leaders/', views.local_leader_list, name='local_leader_list'),
    path('local-leaders/create/', views.create_local_leader, name='create_local_leader'),
    path('local-leaders/edit/<int:pk>/', views.edit_local_leader, name='edit_local_leader'),
    path('local-leaders/delete/<int:pk>/', views.delete_local_leader, name='delete_local_leader'),
    
    # Hospital management
    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('hospitals/create/', views.create_hospital, name='create_hospital'),
    path('hospitals/edit/<int:pk>/', views.edit_hospital, name='edit_hospital'),
    path('hospitals/delete/<int:pk>/', views.delete_hospital, name='delete_hospital'),
    
    # Adopter management
    path('adopters/', views.adopter_list, name='adopter_list'),
    path('adopters/edit/<int:pk>/', views.edit_adopter, name='edit_adopter'),
    path('adopters/delete/<int:pk>/', views.delete_adopter, name='delete_adopter'),
]
