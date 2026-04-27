from django.urls import path

from accounts import views


app_name = "accounts"

urlpatterns = [
    path("gestao-pessoas/", views.gestao_pessoas, name="gestao_pessoas"),
]
