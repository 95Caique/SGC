from django.contrib import admin

from clients.models import Cliente, ContatoCliente


class ContatoClienteInline(admin.TabularInline):
    model = ContatoCliente
    extra = 1


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "tipo", "email", "criado_em")
    list_filter = ("tipo", "empresa")
    search_fields = ("nome", "email", "empresa__nome")
    inlines = [ContatoClienteInline]


@admin.register(ContatoCliente)
class ContatoClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cliente", "telefone", "email")
    list_filter = ("cliente__empresa",)
    search_fields = ("nome", "email", "telefone", "cliente__nome")
