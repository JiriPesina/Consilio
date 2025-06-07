# Redmine/views.py

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

# Importujeme už jen verify_redmine_credentials (verify_api_key už neexistuje)
from .UserVerification import verify_redmine_credentials

from .models import Project, Issue
from Redmine.services.project_handler import sync_projects
from Redmine.services.issue_handler import sync_issues, assign_issue_to_user

User = get_user_model()


# --------- VIEW PRO PROJEKTY A ISSUES ---------

class ProjectsList(APIView):
    """
    GET /api/v1/projects/
    """
    def get(self, request, format=None):
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)


class IssuesList(APIView):
    """
    GET /api/v1/issues/
    """
    def get(self, request, format=None):
        issues = Issue.objects.all()
        serializer = IssueSerializer(issues, many=True)
        return Response(serializer.data)


# --------- (POZOR) VIEW PRO OVĚŘENÍ API KLÍČE ---------
# Pokud ho už nepotřebujete, můžete ho zcela smazat. 
# Ukázka: smažeme api_key_verification, protože už bez username/password nemůžete ověřit klíč.

# @api_view(['POST'])
# def api_key_verification(request):
#     api_key = request.data.get('api_key', '')
#     return Response({'detail': 'Tento endpoint není podporován. Použijte verify_redmine_credentials.'},
#                     status=status.HTTP_400_BAD_REQUEST)


# --------- VIEW PRO SEZNAM A VYTVOŘENÍ UŽIVATELŮ ---------

class UserListView(generics.ListAPIView):
    """
    GET /api/v1/users/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserCreateView(generics.CreateAPIView):
    """
    POST /api/v1/users/create/
    Registrace nového uživatele (validace se děje v UserCreateSerializer).
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer


# --------- VIEW PRO SYNCHRONIZACI (WorkspaceLoad a assign_tasks) ---------

class WorkspaceLoadView(APIView):
    """
    POST /api/v1/workspace/load/
    Synchronizace projektů a úloh z Redmine pro aktuálního uživatele.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        api_key = request.user.API_Key
        if not api_key:
            return Response(
                {"error": "Redmine API klíč není nastaven."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
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

        return Response({"status": "synchronizováno"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_tasks(request):
    """
    POST /api/v1/assign-tasks/
    Přiřazení seznamu úloh (issue_ids) ke konkrétnímu uživateli (user_redmine_id).
    """
    user = request.user
    api_key = getattr(user, 'API_Key', None)
    if not api_key:
        return Response({'error': 'Chybí API klíč pro Redmine.'},
                        status=status.HTTP_400_BAD_REQUEST)

    data = request.data.get('assignments', [])
    results = {'success': [], 'failed': []}

    for grp in data:
        rid = grp.get('user_redmine_id')
        for iid in grp.get('issue_ids', []):
            try:
                assign_issue_to_user(api_key, iid, rid)
                results['success'].append({'issue_id': iid, 'user_redmine_id': rid})
            except requests.RequestException as e:
                results['failed'].append({
                    'issue_id': iid,
                    'user_redmine_id': rid,
                    'error': str(e)
                })

    # Po přiřazení zkusíme znovu synchronizovat úlohy
    try:
        sync_issues(api_key)
    except Exception:
        pass

    return Response(results, status=status.HTTP_200_OK)


# --------- VIEW PRO “UŽIVATEL – MĚ” a “UŽIVATEL – UPDATE” ---------

class UserMeView(APIView):
    """
    GET /api/v1/users/me/
    Vrátí data přihlášeného uživatele: {username, email, API_Key}
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "username": user.username,
            "email":    user.email,
            "API_Key":  user.API_Key
        }
        return Response(data, status=status.HTTP_200_OK)


class UserUpdateView(generics.UpdateAPIView):
    """
    PUT /api/v1/users/update/
    Validuje proti Redmine: (API_Key, username, password).
    Pokud validace projde, uloží se: username, email, password, API_Key, redmine_id, is_superuser.
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)  # tady se volá verify_redmine_credentials
        self.perform_update(serializer)
        return Response({"success": True}, status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        current_pw = request.data.get('current_password')
        new_pw     = request.data.get('new_password')
        if not current_pw or not new_pw:
            return Response(
                {"non_field_errors": ["Vyplňte obě pole."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not user.check_password(current_pw):
            return Response(
                {"non_field_errors": ["Aktuální heslo nesouhlasí"]},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_pw)
        user.save()
        return Response({"success": True}, status=status.HTTP_200_OK)