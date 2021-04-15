from .models import *
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


class MyUserSerializer(UserSerializer):
    user = ProfileSerializer(read_only=True)
    class Meta:
        model=Users
        fields = ['id', 'email', 'username', 'last_login', 'date_joined', 'user']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        p = Profile.objects.get(user_id=data['id'])
        data.update({'profile': ProfileSerializer(p).data})
        return data


class MyUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = Users
        fields = ['id', 'password', 'email', 'first_name', 'last_name', 'access_level', 'gender']

