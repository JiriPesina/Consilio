from django.urls import path
from .views import (
    ProjectsList,
    IssuesList,
    UserListView,
    UserCreateView,
    UserMeView,
    UserUpdateView,
    WorkspaceLoadView,
    assign_tasks,
    ChangePasswordView
)

urlpatterns = [
    # Výpis projektů – GET /api/v1/projects/
    path('projects/', ProjectsList.as_view(),       name='project-list'),
    # Výpis úkolů – GET /api/v1/issues/
    path('issues/',   IssuesList.as_view(),         name='issue-list'),
     # Výpis uživatelů – GET /api/v1/users/
    path('users/',        UserListView.as_view(),   name='user-list'),
    # Registrace uživatele – POST /api/v1/users/create/
    path('users/create/', UserCreateView.as_view(), name='user-create'),
    # Detail přihlášeného uživatele – GET /api/v1/users/me/
    path('users/me/',     UserMeView.as_view(),     name='user-me'),
    # Aktualizace uživatelských údajů – PUT /api/v1/users/update/
    path('users/update/', UserUpdateView.as_view(), name='user-update'),
    # Změna hesla – PUT /api/v1/users/change_password/
    path('users/change_password/', ChangePasswordView.as_view(), name='change-password'),
    # Načtení a synchronizace pracovního prostoru – POST /api/v1/workspace/load/
    path('workspace/load/', WorkspaceLoadView.as_view(), name='workspace-load'),
     # Přiřazení úkolů uživatelům – POST /api/v1/assign-tasks/
    path('assign-tasks/',   assign_tasks,                name='assign-tasks'),
]

