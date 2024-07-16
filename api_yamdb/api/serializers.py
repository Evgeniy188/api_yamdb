from rest_framework import serializers
from rest_framework.exceptions import MethodNotAllowed

from reviews.models import Category, Genre, Title, Review, Comment
from users.models import CustomUser


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def validate_score(self, value):
        if not (1 <= value <= 10):
            raise serializers.ValidationError(
                'Оценка должна быть между 1 и 10'
            )
        return value

    def update(self, instance, validated_data):
        request_method = self.context['request'].method
        if request_method == 'PUT':
            raise MethodNotAllowed("PUT")
        instance = super().update(instance, validated_data)
        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')

    def update(self, instance, validated_data):
        if not isinstance(instance.author, CustomUser):
            raise serializers.ValidationError(
                "Автор должен быть пользователем")
        request_method = self.context['request'].method
        if request_method == 'PUT':
            raise MethodNotAllowed("PUT")
        instance = super().update(instance, validated_data)
        instance.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ('id',)
        model = Category


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ('id',)
        model = Genre


class TitleReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.IntegerField(read_only=True, default=None)

    class Meta:
        model = Title
        fields = '__all__'


class TitleCreateSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug',
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True,
    )

    class Meta:
        model = Title
        fields = '__all__'
