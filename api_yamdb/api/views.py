from django.db.models import Avg
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from reviews.models import Review, Comment, Category, Genre, Title
from users.models import CustomUser
from users.permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly, IsUser
from .mixins import CreateListDestroyViewset
from .serializers import (CategorySerializer, GenreSerializer,
                          TitleSerializer, ReviewSerializer, CommentSerializer)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        # Получаем идентификатор произведения из параметров пути
        title_id = self.kwargs['title_id']
        # Возвращаем набор данных,
        # отфильтрованный по идентификатору произведения
        return Review.objects.filter(title_id=title_id)

    def perform_create(self, serializer):
        # Получаем идентификатор произведения из параметров пути
        title_id = self.kwargs['title_id']
        # Получаем объект произведения по этому идентификатору
        try:
            title = Title.objects.get(id=title_id)
        except Title.DoesNotExist:
            raise Http404('Title not found.')
        # Получаем текущего пользователя (автора отзыва)
        user = self.request.user
        # Проверяем, существует ли уже отзыв от
        # этого пользователя на данное произведение
        if Review.objects.filter(title=title, author=user).exists():
            raise ValidationError(
                'Вы уже оставляли свой отзыв на это произведение!'
            )
        # Сохраняем новый отзыв
        serializer.save(author=user, title=title)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_permissions(self):
        # Определяем права доступа в зависимости от действия (action)
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthorOrReadOnly()]
        if self.action == "create":
            return [IsUser()]
        # По умолчанию разрешаем доступ всем
        return [permissions.AllowAny()]


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny()]

    def get_queryset(self):
        # Получаем идентификатор отзыва из параметров пути
        review_id = self.kwargs['review_id']
        # Возвращаем набор данных, отфильтрованный по идентификатору отзыва
        return Comment.objects.filter(review_id=review_id)

    def perform_create(self, serializer):
        # Получаем идентификатор отзыва из параметров пути
        review_id = self.kwargs['review_id']
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            raise Http404('Review not found.')
        user = self.request.user
        # Сохраняем новый комментарий
        serializer.save(author=user, review=review)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        if not isinstance(user, CustomUser):
            return Response({'detail': 'Only authenticated users can comment'},
                            status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def get_permissions(self):
        # Определяем права доступа в зависимости от действия (action)
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthorOrReadOnly()]
        if self.action == "create":
            return [AllowAny()]
        # По умолчанию разрешаем доступ всем
        return [permissions.AllowAny()]


class CategoryViewSet(CreateListDestroyViewset):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)


class GenreViewSet(CreateListDestroyViewset):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')).order_by('-rating')
    serializer_class = TitleSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        category = get_object_or_404(
            Category, slug=self.request.data.get('category')
        )
        genre = Genre.objects.filter(
            slug__in=self.request.data.getlist('genre')
        )
        serializer.save(category=category, genre=genre)

    def perform_update(self, serializer):
        self.perform_create(serializer)

    def get_queryset(self):
        queryset = super().get_queryset()
        genre_slug = self.request.query_params.get('genre')
        if genre_slug:
            queryset = queryset.filter(genre__slug=genre_slug)
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        title_year = self.request.query_params.get('year')
        if title_year:
            queryset = queryset.filter(year=int(title_year))
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name=name)
        return queryset
