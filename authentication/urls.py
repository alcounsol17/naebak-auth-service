from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('refresh-token/', views.refresh_token, name='refresh_token'),
    
    # User profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('user-info/', views.user_info, name='user_info'),
    path('change-password/', views.change_password, name='change_password'),
    
    # History and monitoring
    path('login-history/', views.LoginHistoryView.as_view(), name='login_history'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
]
