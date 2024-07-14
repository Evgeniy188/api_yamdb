from django.urls import path
from .views import SignupView, CreateTokenView


app_name = 'auth_app'


urlpatterns = [
    path('v1/auth/signup/', SignupView.as_view(), name='user-signup'),
    path('v1/auth/token/', CreateTokenView.as_view(),
         name='token-generation'),
]
