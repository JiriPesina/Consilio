from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Issue

admin.site.register(Issue)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'API_Key', 'redmine_id', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Vlastní Redmine pole', {'fields': ('API_Key', 'redmine_id')}),
    )