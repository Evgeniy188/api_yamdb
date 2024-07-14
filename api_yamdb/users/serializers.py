from rest_framework import serializers
from rest_framework.exceptions import MethodNotAllowed
from .models import CustomUser as User
from .roles import RoleEnum


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'bio', 'last_name',
                  'username', 'email', 'role')

    def validate_email(self, value):
        if (User.objects.filter(email=value)
                .exclude(pk=self.instance.pk).exists()):
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate_name(self, value):
        if (User.objects.filter(name=value)
                .exclude(pk=self.instance.pk).exists()):
            raise serializers.ValidationError("Name already exists.")
        return value

    def update(self, instance, validated_data):
        validated_data.pop('role', None)
        bio = validated_data.get('bio')
        instance = super().update(instance, validated_data)
        if bio is not None:
            instance.bio = bio
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'bio', 'role']


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'bio', 'role']

        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'first_name': {'required': False, 'default': ''},
            'last_name': {'required': False, 'default': ''},
            'bio': {'required': False, 'default': ''},
            'role': {'required': False, 'default': RoleEnum.USER.value},
        }

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        if not email:
            raise serializers.ValidationError("email is required")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists.")
        if User.objects.filter(username=username).exists():
            raise serializers.ValidatationError("Username already exists.")
        return data

    def create(self, validated_data):
        validated_data.setdefault('first_name', '')
        validated_data.setdefault('last_name', '')
        validated_data.setdefault('bio', '')
        validated_data.setdefault('role', RoleEnum.USER.value)
        validated_data['is_admin'] = (validated_data['role']
                                      == RoleEnum.ADMIN.value)

        user = User.objects.create(**validated_data)
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'bio', 'role']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'bio', 'role']

    def update(self, instance, validated_data):
        request_method = self.context['request'].method
        if request_method == 'PUT':
            raise MethodNotAllowed("PUT")
        bio = validated_data.get('bio')
        validated_data.pop('role', None)
        instance = super().update(instance, validated_data)
        if bio is not None:
            instance.bio = bio
        instance.save()
        return instance
