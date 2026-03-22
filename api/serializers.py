"""API serializers."""

from rest_framework import serializers

from catalog.models import Category, Certification, TestBank


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']


class CertificationSerializer(serializers.ModelSerializer):
    """Serializer for Certification."""

    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Certification
        fields = ['id', 'name', 'slug', 'category', 'category_name', 'difficulty_level', 'description']


class TestBankListSerializer(serializers.ModelSerializer):
    """Serializer for TestBank list (minimal fields)."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = TestBank
        fields = [
            'id', 'title', 'slug', 'description', 'price', 'difficulty_level',
            'category_name', 'question_count', 'average_rating', 'total_ratings',
        ]

    def get_question_count(self, obj):
        return obj.get_question_count()


class TestBankDetailSerializer(serializers.ModelSerializer):
    """Serializer for TestBank detail."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = TestBank
        fields = [
            'id', 'title', 'slug', 'description', 'price', 'difficulty_level',
            'category_name', 'question_count', 'average_rating', 'total_ratings',
            'time_limit_minutes', 'attempts_per_purchase', 'organization', 'official_url',
        ]

    def get_question_count(self, obj):
        return obj.get_question_count()
