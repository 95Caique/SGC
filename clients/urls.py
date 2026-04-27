from django.urls import path

from clients import views


app_name = "clients"

urlpatterns = [
    path("", views.listar_clientes, name="listar"),
    path("criar/", views.criar_cliente, name="criar"),
    path("<int:cliente_id>/", views.detalhe_cliente, name="detalhe"),
    path("<int:cliente_id>/editar/", views.editar_cliente, name="editar"),
    path("<int:cliente_id>/contatos/criar/", views.criar_contato_cliente, name="criar_contato"),
]
