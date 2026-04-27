from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from contracts.models import Contrato
from core.permissoes import VerificadorPermissoes, requer_autenticacao
from dashboard.services import ServicoPainel
from proposals.models import Proposta


@requer_autenticacao
@require_GET
def interface_institucional(request):
    empresa = _empresa_do_usuario(request.user)

    contratos = Contrato.objects.select_related("cliente").order_by("-criado_em")
    propostas = Proposta.objects.select_related("cliente").order_by("-criado_em")
    if empresa:
        contratos = contratos.filter(empresa=empresa)
        propostas = propostas.filter(empresa=empresa)
    elif not _usuario_tem_acesso_global(request.user):
        contratos = contratos.none()
        propostas = propostas.none()

    contratos = contratos[:12]
    propostas = propostas[:12]
    if empresa or _usuario_tem_acesso_global(request.user):
        metricas = _serializar_decimais(ServicoPainel.obter_metricas_gerais(empresa))
    else:
        metricas = _metricas_vazias()

    return render(
        request,
        "dashboard/interface_institucional.html",
        {
            "empresa": empresa,
            "metricas": metricas,
            "contratos": contratos,
            "propostas": propostas,
            "total_contratos": contratos.count(),
            "total_valor_contratos": sum(contrato.valor_mensal for contrato in contratos),
            "total_propostas": propostas.count(),
            "total_valor_propostas": sum(proposta.valor_final for proposta in propostas),
            "menu_ativo": "painel",
        },
    )


@requer_autenticacao
@require_GET
def administracao(request):
    return render(request, "dashboard/administracao.html")


@requer_autenticacao
@require_GET
def central_servicos(request):
    return render(request, "dashboard/central_servicos.html")


@requer_autenticacao
@require_GET
def relatorios(request):
    empresa = _empresa_do_usuario(request.user)
    if not empresa and not _usuario_tem_acesso_global(request.user):
        contexto = {
            "metricas": {
                "total_contratos_ativos": 0,
                "total_clientes": 0,
                "faturamento_mensal": "0.00",
                "propostas_pendentes": 0,
            },
            "saude_contratos": {},
            "saude_propostas": {},
            "faturamento_clientes": [],
            "contratos_vencimento": [],
            "propostas_pendentes": [],
        }
    else:
        contexto = {
            "metricas": _serializar_decimais(ServicoPainel.obter_metricas_gerais(empresa)),
            "saude_contratos": ServicoPainel.obter_saude_contratos(empresa),
            "saude_propostas": ServicoPainel.obter_saude_propostas(empresa),
            "faturamento_clientes": [
                _serializar_decimais(item)
                for item in ServicoPainel.obter_faturamento_por_cliente(empresa)[:10]
            ],
            "contratos_vencimento": ServicoPainel.obter_contratos_proximos_vencimento(empresa, dias=60)[:10],
            "propostas_pendentes": ServicoPainel.obter_propostas_pendentes(empresa)[:10],
        }
    return render(request, "dashboard/relatorios.html", contexto)


@requer_autenticacao
@require_GET
def metricas_gerais(request):
    empresa = _empresa_do_usuario(request.user)
    if not empresa and not _usuario_tem_acesso_global(request.user):
        return JsonResponse(
            {
                "total_contratos_ativos": 0,
                "total_clientes": 0,
                "faturamento_mensal": "0.00",
                "propostas_pendentes": 0,
            }
        )
    return JsonResponse(_serializar_decimais(ServicoPainel.obter_metricas_gerais(empresa)))


@requer_autenticacao
@require_GET
def contratos_proximos_vencimento(request):
    empresa = _empresa_do_usuario(request.user)
    if not empresa and not _usuario_tem_acesso_global(request.user):
        return JsonResponse({"resultados": []})
    dias = int(request.GET.get("dias", 30))
    contratos = ServicoPainel.obter_contratos_proximos_vencimento(empresa, dias=dias)
    return JsonResponse(
        {
            "resultados": [
                {
                    "id": contrato.id,
                    "cliente": {
                        "id": contrato.cliente_id,
                        "nome": contrato.cliente.nome,
                    },
                    "titulo": contrato.titulo,
                    "valor_mensal": str(contrato.valor_mensal),
                    "data_fim": contrato.data_fim.isoformat() if contrato.data_fim else None,
                    "dias_para_expiracao": contrato.dias_para_expiracao(),
                }
                for contrato in contratos
            ]
        }
    )


@requer_autenticacao
@require_GET
def propostas_pendentes(request):
    empresa = _empresa_do_usuario(request.user)
    if not empresa and not _usuario_tem_acesso_global(request.user):
        return JsonResponse({"resultados": []})
    propostas = ServicoPainel.obter_propostas_pendentes(empresa)
    return JsonResponse(
        {
            "resultados": [
                {
                    "id": proposta.id,
                    "cliente": {
                        "id": proposta.cliente_id,
                        "nome": proposta.cliente.nome,
                    },
                    "titulo": proposta.titulo,
                    "valor_final": str(proposta.valor_final),
                    "status": proposta.status,
                    "valido_ate": proposta.valido_ate.isoformat() if proposta.valido_ate else None,
                }
                for proposta in propostas
            ]
        }
    )


@requer_autenticacao
@require_GET
def faturamento_por_cliente(request):
    empresa = _empresa_do_usuario(request.user)
    if not empresa and not _usuario_tem_acesso_global(request.user):
        return JsonResponse({"resultados": []})
    relatorio = ServicoPainel.obter_faturamento_por_cliente(empresa)
    return JsonResponse(
        {
            "resultados": [
                _serializar_decimais(item)
                for item in relatorio
            ]
        }
    )


@requer_autenticacao
@require_GET
def saude(request):
    empresa = _empresa_do_usuario(request.user)
    if not empresa and not _usuario_tem_acesso_global(request.user):
        return JsonResponse(
            {
                "contratos": {"total": 0, "ativos": 0, "expirados": 0, "cancelados": 0, "suspensos": 0, "encerrados": 0},
                "propostas": {"total": 0, "rascunhos": 0, "enviadas": 0, "aceitas": 0, "rejeitadas": 0, "expiradas": 0, "convertidas": 0},
            }
        )
    return JsonResponse(
        {
            "contratos": ServicoPainel.obter_saude_contratos(empresa),
            "propostas": ServicoPainel.obter_saude_propostas(empresa),
        }
    )


def _serializar_decimais(dados):
    return {
        chave: f"{valor:.2f}" if hasattr(valor, "as_tuple") else valor
        for chave, valor in dados.items()
    }


def _metricas_vazias():
    return {
        "total_contratos_ativos": 0,
        "total_clientes": 0,
        "faturamento_mensal": "0.00",
        "propostas_pendentes": 0,
    }


def _usuario_tem_acesso_global(usuario):
    return VerificadorPermissoes.usuario_tem_acesso_global(usuario)


def _empresa_do_usuario(usuario):
    return None if _usuario_tem_acesso_global(usuario) else usuario.empresa
