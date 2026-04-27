from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


class VerificadorPermissoes:
    @staticmethod
    def usuario_pode_criar(usuario):
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.funcao in [usuario.Funcao.ADMINISTRADOR, usuario.Funcao.GERENCIADOR]
        )

    @staticmethod
    def usuario_pode_editar(usuario):
        return bool(usuario and usuario.is_authenticated and usuario.pode_editar())

    @staticmethod
    def usuario_pode_deletar(usuario):
        return bool(usuario and usuario.is_authenticated and usuario.pode_deletar())

    @staticmethod
    def usuario_pertence_empresa(usuario, empresa):
        return bool(
            usuario
            and usuario.is_authenticated
            and getattr(usuario, "empresa_id", None)
            and empresa
            and usuario.empresa_id == empresa.id
        )

    @staticmethod
    def usuario_pode_acessar_recurso(usuario, recurso):
        empresa = getattr(recurso, "empresa", None)
        return VerificadorPermissoes.usuario_pertence_empresa(usuario, empresa)


def _bloquear_se_falso(verificacao):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not verificacao(request.user):
                return HttpResponseForbidden("Permissao negada.")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def requer_autenticacao(view_func):
    return login_required(view_func)


def requer_criacao(view_func):
    return login_required(
        _bloquear_se_falso(VerificadorPermissoes.usuario_pode_criar)(view_func)
    )


def requer_edicao(view_func):
    return login_required(
        _bloquear_se_falso(VerificadorPermissoes.usuario_pode_editar)(view_func)
    )


def requer_delecao(view_func):
    return login_required(
        _bloquear_se_falso(VerificadorPermissoes.usuario_pode_deletar)(view_func)
    )
