import logging
import re

from api.roles import RoleEnum
from api.utils import generate_confirmation_code, send_confirmation_email
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import MethodNotAllowed
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import CinemaUser as User

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Review
        fields = ['id', 'text', 'author', 'score', 'pub_date']

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
        fields = ['id', 'text', 'author', 'pub_date']

    def update(self, instance, validated_data):
        if not instance.author.is_authenticated:
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
        exclude = ['id']
        model = Category


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ['id']
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

    def to_representation(self, instance):
        serializer = TitleReadSerializer(instance)
        return serializer.data

    def update(self, instance, validated_data):
        request_method = self.context['request'].method
        if request_method == 'PUT':
            raise MethodNotAllowed("PUT")
        instance = super().update(instance, validated_data)
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'bio', 'role']

    def __init__(self, *args, **kwargs):
        super(UserSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request', None)

        if request:
            if request.method == 'GET':
                if 'pk' in request.parser_context['kwargs']:
                    self.fields['role'].read_only = True
            elif request.method == 'POST':
                # Create view
                self.fields['username'].required = True
                self.fields['email'].required = True
                self.fields['first_name'].required = False
                self.fields['last_name'].required = False
                self.fields['bio'].required = False
                self.fields['role'].required = False
            elif request.method in ['PUT', 'PATCH']:
                self.fields['role'].read_only = False

    def validate(self, data):
        request = self.context.get('request', None)
        if request:
            if request.method == 'POST':
                email = data.get('email')
                username = data.get('username')
                if not email:
                    raise serializers.ValidationError("email is required")
                if User.objects.filter(email=email).exists():
                    raise serializers.ValidationError("Email already exists.")
                if User.objects.filter(username=username).exists():
                    raise serializers.ValidationError(
                        "Username already exists.")
            role = data.get('role')
            if role and role not in RoleEnum.values:
                raise serializers.ValidationError("Invalid role.")
        return data

    def validate_role(self, value):
        if value not in RoleEnum.values:
            raise serializers.ValidationError("Invalid role.")
        return value

    def create(self, validated_data):
        validated_data.setdefault('first_name', '')
        validated_data.setdefault('last_name', '')
        validated_data.setdefault('bio', '')
        validated_data.setdefault('role', RoleEnum.USER.value)

        user = User.objects.create(**validated_data)
        return user

    def update(self, instance, validated_data):
        request = self.context.get('request', None)
        if request and request.method == 'PUT':
            raise MethodNotAllowed("PUT")
        bio = validated_data.get('bio')
        validated_data.pop('role', None)
        instance = super().update(instance, validated_data)
        if bio is not None:
            instance.bio = bio
        instance.save()
        return instance


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        required=False,
        validators=[],
        error_messages={
            'blank': 'This field may not be blank.',
            'required': 'This field is required.',
            'unique': 'A user with that username already exists.',
        }
    )
    email = serializers.EmailField(
        required=False, max_length=254,
        error_messages={
            'blank': 'This field may not be blank.',
            'required': 'This field is required.',
            'unique': 'A user with that email already exists.',
            'invalid': 'Enter a valid email address.',
        }
    )

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
                "Username must contain only letters, "
                "numbers, dots, underscores, and dashes")
        return value

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        errors = {}

        if not username:
            errors['username'] = 'This field is required.'
        if not email:
            errors['email'] = 'This field is required.'

        if errors:
            raise serializers.ValidationError(errors)

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if user.email != email:
                raise serializers.ValidationError({
                    'email': 'Email does not match the registered username.'
                })
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            if user.username != username:
                raise serializers.ValidationError({
                    'username': 'Wrong username'
                })

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
        confirmation_code = generate_confirmation_code()
        user.confirmation_code = confirmation_code
        user.save()

        send_confirmation_email(user.email, confirmation_code)
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
        user = get_object_or_404(User, username=username)

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
