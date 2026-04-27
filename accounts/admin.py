from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import UsuarioCustomizado


@admin.register(UsuarioCustomizado)
class UsuarioCustomizadoAdmin(UserAdmin):
    list_display = ("username", "email", "empresa", "funcao", "is_active", "is_staff")
    list_filter = ("funcao", "empresa", "is_active", "is_staff")
    search_fields = ("username", "email", "empresa__nome")
    fieldsets = UserAdmin.fieldsets + (
        ("ContraFlow", {"fields": ("empresa", "funcao")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("ContraFlow", {"fields": ("empresa", "funcao")}),
    )
