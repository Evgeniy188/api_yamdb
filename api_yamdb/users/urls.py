from django.urls import path
from .views import UserProfileUpdateView, UserListCreateView, UserDetailView


app_name = 'users'


urlpatterns = [
    path('v1/users/me/', UserProfileUpdateView.as_view(), name='user_update'),
    path('v1/users/', UserListCreateView.as_view(), name='user_list'),
    path('v1/users/<str:username>/',
         UserDetailView.as_view(), name='user_detail')
]
