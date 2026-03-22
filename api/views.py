"""API views."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from catalog.models import Category, Certification, TestBank

from .serializers import (
    CategorySerializer,
    CertificationSerializer,
    TestBankDetailSerializer,
    TestBankListSerializer,
)


class CategoryListAPIView(generics.ListAPIView):
    """List all categories."""

    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CertificationListAPIView(generics.ListAPIView):
    """List certifications, optionally filtered by category."""

    serializer_class = CertificationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Certification.objects.select_related('category').order_by('order', 'name')
        category_slug = self.request.query_params.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs


class TestBankListAPIView(generics.ListAPIView):
    """List active test banks."""

    serializer_class = TestBankListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return (
            TestBank.objects.filter(is_active=True)
            .select_related('category')
            .order_by('-created_at')
        )


class TestBankDetailAPIView(generics.RetrieveAPIView):
    """Retrieve a single test bank by slug."""

    queryset = TestBank.objects.filter(is_active=True).select_related('category')
    serializer_class = TestBankDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'
