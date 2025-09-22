"""
URLs للمراقبة والمقاييس
"""
from django.urls import path
from .monitoring import metrics_view
from .views import health_check

urlpatterns = [
    path('metrics/', metrics_view, name='metrics'),
    path('health/', health_check, name='health_check'),
]
