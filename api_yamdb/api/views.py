from django.db.models import Avg
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (filters, generics, mixins, permissions,
                            serializers, status, viewsets)
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import CinemaUser as User

from .filters import TitleFilter
from .permissions import IsAdmin, IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (CategorySerializer, CommentSerializer,
                          CreateTokenSerializer, GenreSerializer,
                          ReviewSerializer, SignupSerializer,
                          TitleCreateSerializer, TitleReadSerializer,
                          UserSerializer)


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
            return [IsAuthenticated()]
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
        if not user.is_authenticated:
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


class CreateListDestroyViewset(
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        mixins.DestroyModelMixin,
        viewsets.GenericViewSet,
):
    search_fields = ('name', )
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, )
    permission_classes = (IsAdminOrReadOnly, )


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
        rating=Avg('reviews__score')).order_by('-rating', 'name')
    permission_classes = (IsAdminOrReadOnly, )
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return TitleCreateSerializer
        return TitleReadSerializer


class UserViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'username'
    filter_backends = [SearchFilter]
    search_fields = ['username']

    def perform_create(self, serializer):
        if 'email' not in self.request.data:
            raise serializers.ValidationError({
                'detail': 'Only authenticated users can comment'})
        serializer.save()

    @action(detail=False, methods=['get', 'patch'],
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        partial = True
        data = dict(request.data)
        data.pop('role', None)
        serializer = self.get_serializer(request.user,
                                         data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdmin])
    def update_profile(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        raise MethodNotAllowed('PUT')


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]
    renderer_classes = [JSONRenderer]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateTokenView(generics.CreateAPIView):
    serializer_class = CreateTokenSerializer
    permission_classes = [permissions.AllowAny]
    renderer_classes = [JSONRenderer]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.save()
        return Response({"token": token["access"]}, status=status.HTTP_200_OK)
