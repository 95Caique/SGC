from django.shortcuts import render
from django.views.decorators.http import require_GET

from companies.models import Empresa
from core.permissoes import VerificadorPermissoes, requer_autenticacao


@requer_autenticacao
@require_GET
def listar_empresas(request):
    empresas = Empresa.objects.order_by("nome")
    if not VerificadorPermissoes.usuario_tem_acesso_global(request.user):
        empresas = Empresa.objects.filter(id=request.user.empresa_id) if request.user.empresa_id else Empresa.objects.none()
    return render(
        request,
        "companies/lista.html",
        {
            "empresas": empresas,
            "total_empresas": empresas.count(),
        },
    )
