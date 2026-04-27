from django.urls import path

from dashboard import views


app_name = "dashboard"

urlpatterns = [
    path("metricas/", views.metricas_gerais, name="metricas"),
    path("contratos-vencimento/", views.contratos_proximos_vencimento, name="contratos_vencimento"),
    path("propostas-pendentes/", views.propostas_pendentes, name="propostas_pendentes"),
    path("faturamento-clientes/", views.faturamento_por_cliente, name="faturamento_clientes"),
    path("saude/", views.saude, name="saude"),
]
