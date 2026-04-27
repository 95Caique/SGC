from django.shortcuts import render
from django.views.decorators.http import require_GET

from accounts.models import UsuarioCustomizado
from core.permissoes import VerificadorPermissoes, requer_autenticacao


@requer_autenticacao
@require_GET
def gestao_pessoas(request):
    usuarios = UsuarioCustomizado.objects.order_by("username")
    if not VerificadorPermissoes.usuario_tem_acesso_global(request.user):
        usuarios = usuarios.filter(empresa=request.user.empresa)
    return render(
        request,
        "accounts/gestao_pessoas.html",
        {
            "usuarios": usuarios,
            "total_usuarios": usuarios.count(),
        },
    )
