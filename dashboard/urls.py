from django.urls import path

from dashboard import views


app_name = "dashboard"

urlpatterns = [
    path("", views.interface_institucional, name="interface"),
    path("administracao/", views.administracao, name="administracao"),
    path("central-servicos/", views.central_servicos, name="central_servicos"),
    path("relatorios/", views.relatorios, name="relatorios"),
    path("metricas/", views.metricas_gerais, name="metricas"),
    path("contratos-vencimento/", views.contratos_proximos_vencimento, name="contratos_vencimento"),
    path("propostas-pendentes/", views.propostas_pendentes, name="propostas_pendentes"),
    path("faturamento-clientes/", views.faturamento_por_cliente, name="faturamento_clientes"),
    path("saude/", views.saude, name="saude"),
]
