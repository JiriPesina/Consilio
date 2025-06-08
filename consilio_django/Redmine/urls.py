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
    path('projects/', ProjectsList.as_view(),       name='project-list'),
    path('issues/',   IssuesList.as_view(),         name='issue-list'),
    path('users/',        UserListView.as_view(),   name='user-list'),
    path('users/create/', UserCreateView.as_view(), name='user-create'),
    path('users/me/',     UserMeView.as_view(),     name='user-me'),
    path('users/update/', UserUpdateView.as_view(), name='user-update'),
    path('users/change_password/', ChangePasswordView.as_view(), name='change-password'),
    path('workspace/load/', WorkspaceLoadView.as_view(), name='workspace-load'),
    path('assign-tasks/',   assign_tasks,                name='assign-tasks'),
]

