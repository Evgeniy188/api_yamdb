from rest_framework import serializers
from rest_framework.exceptions import MethodNotAllowed, ValidationError

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

    def validate(self, data):
        request = self.context['request']
        if request.method == 'POST':
            user = request.user
            title_id = request.parser_context['kwargs']['title_id']
            if Review.objects.filter(title_id=title_id, author=user).exists():
                raise ValidationError(
                    'Вы уже оставляли отзыв на это произведение'
                )
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ['id']
        model = Category


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ['id']
        model = Genre


class TitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Title
        fields = '__all__'

    def update(self, instance, validated_data):
        request_method = self.context['request'].method
        if request_method == 'PUT':
            raise MethodNotAllowed("PUT")
        instance = super().update(instance, validated_data)
        instance.save()
        return instance
