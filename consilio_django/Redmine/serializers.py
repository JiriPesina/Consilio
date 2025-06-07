from rest_framework import serializers
from django.contrib.auth import get_user_model
from .UserVerification import verify_redmine_credentials
from .models import Project, Issue

User = get_user_model()

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = (
            "id",
            "project_id",
            "name",
            "type",
            "status",
            "priority",
            "assigned",
            "completion_percentage",
            "deadline",
        )

class ProjectSerializer(serializers.ModelSerializer):
    issues = IssueSerializer(many=True) 

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "issues",
        )

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'redmine_id']

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pro registraci nového uživatele.
    Při vytvoření:
      1) Ověříme api_key, username, password v Redmine (GET /my/account.json).
      2) Z odpovědi uložíme redmine_id a is_superuser.
      3) Pokud cokoliv selže, vrátíme  ValidationError("Zadané údaje nesouhlasí s Redmine").
      4) Uložíme nového uživatele (včetně API_Key, redmine_id, is_superuser).
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
       
        fields = ['username', 'email', 'password', 'API_Key']

    def validate(self, data):
        """
        Validace před samotným vytvořením. Zavoláme Redmine a ověříme,
        že (username,password,API_Key) existují. Pokud ne, vyhodíme chybu.
        """
        api_key = data.get('API_Key')
        username = data.get('username')
        password = data.get('password')

   
        try:
            response = verify_redmine_credentials(api_key, username, password)
        except Exception as e:
           raise serializers.ValidationError("Chyba komunikace s Redmine: %r" % e)

        if response.status_code != 200:
            raise serializers.ValidationError("Zadané údaje nesouhlasí s Redmine")
        
        payload = response.json()

        if 'user' in payload:
            redmine_user = payload['user']
        else:
            redmine_user = payload

        if not redmine_user.get('id') or 'admin' not in redmine_user:
            raise serializers.ValidationError("Neočekávaná struktura odpovědi z Redmine")

        self._validated_redmine_id = redmine_user['id']
        self._validated_is_admin    = redmine_user['admin']
        return data

    def create(self, validated_data):
        username = validated_data.get('username')
        email    = validated_data.get('email')
        password = validated_data.get('password')
        api_key  = validated_data.get('API_Key')

        user = User(
            username=username,
            email=email,
        )
        user.set_password(password)
        user.API_Key     = api_key
        user.redmine_id  = self._validated_redmine_id
        user.is_superuser = self._validated_is_admin
        user.save()
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    API_Key  = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'API_Key']

    def validate(self, data):
        api_key  = data.get('API_Key')
        username = data.get('username')
        try:
            response = verify_redmine_credentials(api_key, username)
        except Exception as e:

            raise serializers.ValidationError(f"Chyba při volání Redmine: {e}")

        if response.status_code != 200:
            raise serializers.ValidationError("Nové údaje nesouhlasí s údaji v Redmine")

        payload = response.json()

        redmine_user = payload.get('user', payload)

        if not redmine_user.get('id') or 'admin' not in redmine_user:
            raise serializers.ValidationError("Neočekávaná struktura odpovědi z Redmine")

        self._validated_redmine_id = redmine_user['id']
        self._validated_is_admin    = redmine_user['admin']

        return data

    def update(self, instance, validated_data):

        instance.username = validated_data.get('username', instance.username)
        instance.email    = validated_data.get('email', instance.email)
        instance.API_Key = validated_data.get('API_Key', instance.API_Key)
        instance.redmine_id   = self._validated_redmine_id
        instance.is_superuser = self._validated_is_admin

        instance.save()
        return instance

