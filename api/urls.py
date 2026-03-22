"""API URL configuration."""

from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = 'api'

urlpatterns = [
    # JWT auth
    path('v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('v1/categories/', views.CategoryListAPIView.as_view(), name='category-list'),
    path('v1/certifications/', views.CertificationListAPIView.as_view(), name='certification-list'),
    path('v1/test-banks/', views.TestBankListAPIView.as_view(), name='testbank-list'),
    path('v1/test-banks/<slug:slug>/', views.TestBankDetailAPIView.as_view(), name='testbank-detail'),
]
