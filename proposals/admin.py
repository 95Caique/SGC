from django.contrib import admin

from proposals.models import Proposta, PropostaHistorico


@admin.register(Proposta)
class PropostaAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "empresa",
        "cliente",
        "status",
        "valor",
        "desconto",
        "valor_final",
        "valido_ate",
    )
    list_filter = ("status", "empresa")
    search_fields = ("titulo", "cliente__nome", "empresa__nome")
    readonly_fields = ("valor_final",)


@admin.register(PropostaHistorico)
class PropostaHistoricoAdmin(admin.ModelAdmin):
    list_display = ("proposta", "acao", "usuario", "criado_em")
    list_filter = ("acao", "proposta__empresa")
    search_fields = ("proposta__titulo", "usuario__username")
    readonly_fields = ("dados", "criado_em")
