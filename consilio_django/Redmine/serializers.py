from rest_framework import serializers
from django.contrib.auth import get_user_model
from .UserVerification import verify_redmine_credentials
from .models import Project, Issue

User = get_user_model()


class IssueSerializer(serializers.ModelSerializer):
    # Přidáváme virtuální pole project_parent_id, které přečte parent_id z navázaného projektu.
    project_parent_id = serializers.IntegerField(
        source='project_id.parent_id',
        read_only=True
    )

    class Meta:
        model = Issue
        fields = (
            "id",
            "project_id",
            "project_parent_id",
            "name",
            "type",
            "status",
            "priority",
            "assigned",
            "completion_percentage",
            "deadline",
        )


class ProjectSerializer(serializers.ModelSerializer):
    # Serializér vnoří všechny úkoly patřící k projektu pomocí IssueSerializer
    issues = IssueSerializer(many=True)
    parent_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "issues",
            "parent_id",
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'redmine_id','is_superuser']

#  Serializer pro registraci nového uživatele.
class UserCreateSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'API_Key']

    def validate(self, data):
        #  Ověřuje zadané údaje proti Redmine. Pokud API klíč nebo údaje nesedí, vyvolá chybu.
        api_key = data.get('API_Key')
        username = data.get('username')
        password = data.get('password')

        try:
            response = verify_redmine_credentials(api_key, username, password)
        except Exception as e:
            raise serializers.ValidationError(f"Chyba komunikace s Redmine: {e!r}")

        if response.status_code != 200:
            raise serializers.ValidationError("Zadané údaje nesouhlasí s Redmine")

        payload = response.json()
        redmine_user = payload.get('user', payload)

        if not redmine_user.get('id') or 'admin' not in redmine_user:
            raise serializers.ValidationError("Neočekávaná struktura odpovědi z Redmine")

        self._validated_redmine_id = redmine_user['id']
        self._validated_is_admin = redmine_user['admin']
        return data

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.API_Key = validated_data['API_Key']
        user.redmine_id = self._validated_redmine_id
        user.is_superuser = self._validated_is_admin
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    API_Key = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'API_Key']

    def validate(self, data):
        if 'API_Key' in data:
            api_key = data['API_Key']
            username = data.get('username', self.instance.username)
            response = verify_redmine_credentials(api_key, username, password='')
            if response.status_code != 200:
                raise serializers.ValidationError("API klíč/uživatel nesouhlasí s Redmine.")
            user = response.json().get('user', response.json())
            self._validated_redmine_id = user['id']
            self._validated_is_admin = user['admin']
        else:
            self._validated_redmine_id = self.instance.redmine_id
            self._validated_is_admin = self.instance.is_superuser
        return data

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.API_Key = validated_data.get('API_Key', instance.API_Key)
        instance.redmine_id = self._validated_redmine_id
        instance.is_superuser = self._validated_is_admin
        instance.save()
        return instance