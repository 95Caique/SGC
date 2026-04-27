from django.contrib import admin

from companies.models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cnpj", "email", "telefone", "criado_em")
    search_fields = ("nome", "cnpj", "email")
