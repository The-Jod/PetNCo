from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register your models here.
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('RutUsuario', 'EmailUsuario', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('RutUsuario', 'EmailUsuario')
    ordering = ('RutUsuario',)

admin.site.register(CustomUser, CustomUserAdmin)