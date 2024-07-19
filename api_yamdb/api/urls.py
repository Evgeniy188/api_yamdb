from django.urls import include, path
from rest_framework import routers
from rest_framework.routers import DefaultRouter

from .views import (CategoryViewSet, CommentViewSet, CreateTokenView,
                    GenreViewSet, ReviewViewSet, SignupView, TitleViewSet,
                    UserViewSet)

router_v1 = routers.DefaultRouter()
router_v1.register('categories', CategoryViewSet, basename='categories')
router_v1.register('genres', GenreViewSet, basename='genres')
router_v1.register('titles', TitleViewSet, basename='titles')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='review'
)
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comment'
)

router = DefaultRouter()
router.register(r'v1/users', UserViewSet, basename='user')


urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('', include(router.urls)),
    path('v1/auth/signup/', SignupView.as_view(), name='user-signup'),
    path('v1/auth/token/', CreateTokenView.as_view(),
         name='token-generation'),
]
