from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('google-auth/', views.google_auth, name='google_auth'),
    path('logout/', views.logout, name='logout'),
    path('refresh-token/', views.refresh_token, name='refresh_token'),
    
    # Password management
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Email verification
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    # User profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('user-info/', views.user_info, name='user_info'),
    
    # History and monitoring
    path('login-history/', views.LoginHistoryView.as_view(), name='login_history'),
    path('statistics/', views.user_statistics, name='user_statistics'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
]
