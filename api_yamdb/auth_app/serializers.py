import re
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import NotFound

from users.models import CustomUser as User
from users.roles import RoleEnum
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email')
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False}
        }

    def __init__(self, *args, **kwargs):
        super(SignupSerializer, self).__init__(*args, **kwargs)
        # Без этого назначения падает с ошибкой при существующих username
        self.fields['username'].validators = [self.validate_username]

    def validate_username(self, value):
        RESTRICTED_USERNAMES = ('me',)
        MAX_USERNAME_LENGTH = 150
        USERNAME_PATTERN = r'^[\w.@+-]+\Z'

        if value.lower() in RESTRICTED_USERNAMES:
            raise serializers.ValidationError('Username is restricted')
        if len(value) > MAX_USERNAME_LENGTH:
            raise serializers.ValidationError('Username is too long')
        if not re.match(USERNAME_PATTERN, value):
            raise serializers.ValidationError(
                "Username must contain only letters,"
                "numbers, dots, underscores, and dashes")
        return value

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        if not username or not email:
            # raise serializers.ValidationError(['username', 'email'])
            raise serializers.ValidationError({
                'username': 'required',
                'email': 'required'
            })
        logger.info(f'username: {username}, email: {email}')

        # Check if the user exists and the email matches
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if user.email != email:
                raise serializers.ValidationError(
                    "Email does not match the registered username.")
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            if user.username != username:
                raise serializers.ValidationError("Wrong username")
        return data

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']

        # Check if the user already exists
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email,
                      'is_active': False, 'role': RoleEnum.USER.value}
        )
        return user


class CreateTokenSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    confirmation_code = serializers.CharField(max_length=6)

    class Meta:
        fields = ['username', 'confirmation_code']

    def validate(self, data):
        username = data.get('username')
        confirmation_code = data.get('confirmation_code')

        # Validate the username exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise NotFound("User not found.")

        # Validate the confirmation code
        if user.confirmation_code != confirmation_code:
            raise serializers.ValidationError("Invalid confirmation code.")

        data['user'] = user
        return data

    def create(self, validated_data):
        user = validated_data['user']
        user.is_active = True
        user.save()
        access = AccessToken.for_user(user)
        return {
            'access': str(access),
        }
