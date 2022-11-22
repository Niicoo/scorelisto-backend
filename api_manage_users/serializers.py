from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from api_manage_users.validators import UsernameValidator
from api_manage_users.validators import PasswordValidator
from api_manage_users.validators import BodyContactValidator
from api_manage_users.validators import PhoneContactValidator
from api_manage_users.validators import NameContactValidator


class UserContactSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, validators=[NameContactValidator, ])
    email = serializers.EmailField(required=True)
    body = serializers.CharField(required=True, validators=[BodyContactValidator, ])
    phone = serializers.CharField(required=False, allow_blank=True, validators=[PhoneContactValidator, ])


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    username = serializers.CharField(required=True, validators=[UniqueValidator(queryset=User.objects.all()), UsernameValidator])
    password = serializers.CharField(required=True, write_only=True, validators=[PasswordValidator, ])

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], validated_data['email'], validated_data['password'], is_active=False)
        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')


class UserUpdatePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[PasswordValidator, ])

    def validate_new_password(self, value):
        validate_password(value)
        return value


class UserActivateSerializer(serializers.Serializer):
    uidb64 = serializers.CharField(required=True, max_length=100)
    token = serializers.CharField(required=True, max_length=100)


class UserDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, validators=[PasswordValidator, ])


class UserEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class UserUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, validators=[UsernameValidator, ])


class UserSetNewPasswordSerializer(serializers.Serializer):
    uidb64 = serializers.CharField(required=True, max_length=100)
    token = serializers.CharField(required=True, max_length=100)
    password = serializers.CharField(required=True, validators=[PasswordValidator, ])
