from django.contrib import admin

from contracts.models import Contrato, ContratoArquivo, ContratoHistorico


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "empresa",
        "cliente",
        "status",
        "valor_mensal",
        "data_inicio",
        "data_fim",
    )
    list_filter = ("status", "empresa")
    search_fields = ("titulo", "cliente__nome", "empresa__nome")


@admin.register(ContratoArquivo)
class ContratoArquivoAdmin(admin.ModelAdmin):
    list_display = ("contrato", "versao", "enviado_por", "criado_em")
    list_filter = ("contrato__empresa",)
    search_fields = ("contrato__titulo",)


@admin.register(ContratoHistorico)
class ContratoHistoricoAdmin(admin.ModelAdmin):
    list_display = ("contrato", "acao", "usuario", "criado_em")
    list_filter = ("acao", "contrato__empresa")
    search_fields = ("contrato__titulo", "usuario__username")
    readonly_fields = ("dados", "criado_em")
