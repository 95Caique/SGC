from django.urls import path

from companies import views


app_name = "companies"

urlpatterns = [
    path("", views.listar_empresas, name="listar"),
]
