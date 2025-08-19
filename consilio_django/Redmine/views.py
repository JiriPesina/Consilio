import requests
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.contrib.auth import get_user_model

from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ProjectSerializer,
    IssueSerializer
)

from .UserVerification import verify_redmine_credentials
from .models import Project, Issue
from Redmine.services.project_handler import sync_projects
from Redmine.services.issue_handler import sync_issues, assign_issue_to_user

User = get_user_model()

# Vrací seznam všech projektů uložených v databázi. GET /api/v1/projects/
class ProjectsList(APIView):
    def get(self, request, format=None):
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

# Vrací seznam všech úkolů (issues) z databáze.   GET /api/v1/issues/
class IssuesList(APIView):
    def get(self, request, format=None):
        issues = Issue.objects.all()
        serializer = IssueSerializer(issues, many=True)
        return Response(serializer.data)

# Používá generický pohled DRF pro výpis všech uživatelů. GET /api/v1/users/
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Registrace nového uživatele. Validace vstupů (heslo, email, API klíč atd.) probíhá v UserCreateSerializer POST /api/v1/users/create/
class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

# Synchronizuje projekty a úkoly z Redmine pomocí API klíče přihlášeného uživatele POST /api/v1/workspace/load/
class WorkspaceLoadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        api_key = request.user.API_Key
         # Pokud uživatel nemá nastavený API klíč, vrací chybovou odpověď 400
        if not api_key:
            return Response(
                {"error": "Redmine API klíč není dostupný."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Spuštění synchronizace projektů a úkolů z Redmine
            sync_projects(api_key)
            sync_issues(api_key)
        except requests.RequestException as e:
            return Response(
                {"error": f"Chyba při komunikaci s Redmine: {e}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            return Response(
                {"error": f"Neočekávaná chyba: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        # Pokud synchronizace proběhne v pořádku, vrací úspěšnou odpověď
        return Response({"status": "synchronizováno"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
# Přiřazení seznamu úloh (issue_ids) ke konkrétnímu uživateli (user_redmine_id). POST /api/v1/assign-tasks/
def assign_tasks(request):
    user = request.user
    api_key = getattr(user, 'API_Key', None)
    if not api_key:
        return Response({'error': 'Chybí API klíč pro Redmine.'},
                        status=status.HTTP_400_BAD_REQUEST)
    # Z těla požadavku získá pole 'assignments', které obsahuje redmine_id uživatele a seznam ID úkolů
    data = request.data.get('assignments', [])
    results = {'success': [], 'failed': []}
    
    # Projde každou skupinu přiřazení z požadavku (uživatel + úkoly)
    for grp in data:
        rid = grp.get('user_redmine_id')
        for iid in grp.get('issue_ids', []):
            try:
                # Zavolá servisní funkci, která provede přiřazení na Redmine
                assign_issue_to_user(api_key, iid, rid)
                results['success'].append({'issue_id': iid, 'user_redmine_id': rid})
            except requests.RequestException as e:
                 # V případě chyby uloží ID úkolu a uživatele do neúspěšných položek
                results['failed'].append({
                    'issue_id': iid,
                    'user_redmine_id': rid,
                    'error': str(e)
                })
     # Po přiřazení se znovu synchronizují úkoly z Redmine, aby byly aktuální
    try:
        sync_issues(api_key)
    except Exception:
        pass

    return Response(results, status=status.HTTP_200_OK)


# Vrací detail přihlášeného uživatele  GET /api/v1/users/me/
class UserMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Aktualizuje údaje uživatele. Validace probíhá v UserUpdateSerializer. PUT /api/v1/users/update/
class UserUpdateView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Vrací instanci aktuálně přihlášeného uživatele
        return self.request.user

    def update(self, request, *args, **kwargs):
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        # Vyvolá validační logiku serializeru; při chybě se automaticky vrátí 400
        serializer.is_valid(raise_exception=True) 
         # Uloží změny do databáze
        self.perform_update(serializer)
        return Response({"success": True}, status=status.HTTP_200_OK)

# Mění heslo aktuálního uživatele po ověření starého hesla PUT /api/v1/users/change_password/
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        current_pw = request.data.get('current_password')
        new_pw     = request.data.get('new_password')
        # Ověří, že obě hodnoty jsou vyplněné; jinak vrací chybu 400
        if not current_pw or not new_pw:
            return Response(
                {"non_field_errors": ["Vyplňte obě pole."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Kontroluje správnost aktuálního hesla
        if not user.check_password(current_pw):
            return Response(
                {"non_field_errors": ["Aktuální heslo nesouhlasí"]},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Nastaví nové heslo pomocí Django metody set_password a uloží uživatele
        user.set_password(new_pw)
        user.save()
        return Response({"success": True}, status=status.HTTP_200_OK)