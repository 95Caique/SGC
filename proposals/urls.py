from django.urls import path

from proposals import views


app_name = "proposals"

urlpatterns = [
    path("", views.listar_propostas, name="listar"),
    path("criar/", views.criar_proposta, name="criar"),
    path("<int:proposta_id>/", views.detalhe_proposta, name="detalhe"),
    path("<int:proposta_id>/status/", views.alterar_status_proposta, name="alterar_status"),
    path("<int:proposta_id>/converter/", views.converter_proposta_em_contrato, name="converter"),
]
