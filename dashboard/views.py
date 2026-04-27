from django.http import JsonResponse
from django.views.decorators.http import require_GET

from core.permissoes import requer_autenticacao
from dashboard.services import ServicoPainel


@requer_autenticacao
@require_GET
def metricas_gerais(request):
    return JsonResponse(_serializar_decimais(ServicoPainel.obter_metricas_gerais(request.user.empresa)))


@requer_autenticacao
@require_GET
def contratos_proximos_vencimento(request):
    dias = int(request.GET.get("dias", 30))
    contratos = ServicoPainel.obter_contratos_proximos_vencimento(request.user.empresa, dias=dias)
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
    propostas = ServicoPainel.obter_propostas_pendentes(request.user.empresa)
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
    relatorio = ServicoPainel.obter_faturamento_por_cliente(request.user.empresa)
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
    return JsonResponse(
        {
            "contratos": ServicoPainel.obter_saude_contratos(request.user.empresa),
            "propostas": ServicoPainel.obter_saude_propostas(request.user.empresa),
        }
    )


def _serializar_decimais(dados):
    return {
        chave: f"{valor:.2f}" if hasattr(valor, "as_tuple") else valor
        for chave, valor in dados.items()
    }
