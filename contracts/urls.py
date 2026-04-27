from django.urls import path

from contracts import views


app_name = "contracts"

urlpatterns = [
    path("", views.listar_contratos, name="listar"),
    path("criar/", views.criar_contrato, name="criar"),
    path("<int:contrato_id>/", views.detalhe_contrato, name="detalhe"),
    path("<int:contrato_id>/status/", views.alterar_status_contrato, name="alterar_status"),
    path("<int:contrato_id>/arquivos/", views.upload_arquivo_contrato, name="upload_arquivo"),
]
