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
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        title = self.get_title()
        return title.reviews.all()

    def perform_create(self, serializer):
        title = self.get_title()
        user = self.request.user
        serializer.save(author=user, title=title)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthorOrReadOnly()]
        if self.action == "create":
            return [IsUser()]
        return [permissions.AllowAny()]

    def get_title(self):
        title_id = self.kwargs['title_id']
        return get_object_or_404(Title, id=title_id)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        review = self.get_review()
        return review.comments.all()

    def perform_create(self, serializer):
        review = self.get_review()
        user = self.request.user
        serializer.save(author=user, review=review)

    def get_review(self):
        review_id = self.kwargs['review_id']
        return get_object_or_404(Review, id=review_id)


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
