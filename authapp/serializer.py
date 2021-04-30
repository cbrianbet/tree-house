from properties.models import Tenant, CompanyProfile, Companies
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
        fields = ['id', 'email', 'username', 'last_login', 'date_joined', 'user', 'acc_type']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        p = Profile.objects.get(user_id=data['id'])
        data.update({'profile': ProfileSerializer(p).data})
        if data['acc_type'] == 4:
            prop = Tenant.objects.get(profile=Profile.objects.get(user=data['id'])).unit.property
            company = CompanyProfile.objects.get(company=prop.company, user__acc_type_id__in=[2, 3]).user
            landlord = Profile.objects.get(user=company)
            agent = ""
            if company.acc_type.id == 2:
                agent = landlord.first_name + " " + landlord.last_name
            elif company.acc_type.id == 3:
                agent = Companies.objects.get(id=prop.company.id).name
            data.update({'agent': agent})
            data.update({'agent_contact': {'mobile': landlord.msisdn, 'email_address': landlord.user.email}})
        return data


class MyUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = Users
        fields = ['id', 'password', 'email', 'first_name', 'last_name', 'access_level', 'gender']


class PassResetSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    class Meta:
        model = Users
        fields = ['email']


class UpdateUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    id_number = serializers.CharField()
    msisdn = serializers.CharField()

    class Meta:
        model = Users
        fields = ['email', 'first_name', 'last_name', 'id_number', 'msisdn']
