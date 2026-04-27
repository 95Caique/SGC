import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from core.excecoes import ExcecaoContraflow
from core.permissoes import requer_autenticacao, requer_criacao, requer_edicao
from proposals.models import Proposta
from proposals.services import ServicoProposta


@requer_autenticacao
@require_GET
def listar_propostas(request):
    propostas = (
        Proposta.objects.filter(empresa=request.user.empresa)
        .select_related("cliente", "contrato", "criado_por")
        .order_by("-criado_em")
    )
    status = request.GET.get("status")
    if status:
        propostas = propostas.filter(status=status)

    return JsonResponse(
        {
            "resultados": [
                _serializar_proposta(proposta)
                for proposta in propostas
            ]
        }
    )


@requer_criacao
@require_POST
def criar_proposta(request):
    try:
        dados = _obter_json(request)
        proposta = ServicoProposta.criar_proposta(
            empresa_id=request.user.empresa_id,
            cliente_id=dados["cliente_id"],
            titulo=dados["titulo"],
            descricao=dados.get("descricao", ""),
            valor=_decimal(dados["valor"]),
            desconto=_decimal(dados.get("desconto", "0")),
            valido_ate=_data(dados["valido_ate"]) if dados.get("valido_ate") else None,
            criado_por=request.user,
        )
    except (KeyError, InvalidOperation, ValueError) as erro:
        return JsonResponse({"erro": f"Dados invalidos: {erro}"}, status=400)
    except ExcecaoContraflow as erro:
        return JsonResponse({"erro": str(erro)}, status=403)

    return JsonResponse(_serializar_proposta(proposta), status=201)


@requer_autenticacao
@require_GET
def detalhe_proposta(request, proposta_id):
    proposta = _obter_proposta_da_empresa(request, proposta_id)
    return JsonResponse(_serializar_proposta(proposta, incluir_historico=True))


@requer_edicao
@require_POST
def alterar_status_proposta(request, proposta_id):
    proposta = _obter_proposta_da_empresa(request, proposta_id)
    try:
        dados = _obter_json(request)
        status = dados["status"]
        if status == Proposta.Status.ENVIADA:
            proposta = ServicoProposta.marcar_como_enviada(proposta=proposta, usuario=request.user)
        elif status == Proposta.Status.ACEITA:
            proposta = ServicoProposta.aceitar_proposta(proposta=proposta, usuario=request.user)
        elif status == Proposta.Status.REJEITADA:
            proposta = ServicoProposta.rejeitar_proposta(proposta=proposta, usuario=request.user)
        else:
            proposta = ServicoProposta.editar_proposta(
                proposta=proposta,
                usuario=request.user,
                status=status,
            )
    except KeyError as erro:
        return JsonResponse({"erro": f"Campo obrigatorio ausente: {erro}"}, status=400)
    except ExcecaoContraflow as erro:
        return JsonResponse({"erro": str(erro)}, status=400)

    return JsonResponse(_serializar_proposta(proposta))


@requer_edicao
@require_POST
def converter_proposta_em_contrato(request, proposta_id):
    proposta = _obter_proposta_da_empresa(request, proposta_id)
    try:
        contrato = ServicoProposta.converter_em_contrato(
            proposta=proposta,
            usuario=request.user,
        )
    except ExcecaoContraflow as erro:
        return JsonResponse({"erro": str(erro)}, status=400)

    proposta.refresh_from_db()
    return JsonResponse(
        {
            "proposta": _serializar_proposta(proposta),
            "contrato": {
                "id": contrato.id,
                "titulo": contrato.titulo,
                "valor_mensal": str(contrato.valor_mensal),
                "status": contrato.status,
            },
        },
        status=201,
    )


def _obter_proposta_da_empresa(request, proposta_id):
    if not request.user.empresa_id:
        raise Http404
    return get_object_or_404(
        Proposta.objects.select_related("cliente", "contrato", "criado_por"),
        id=proposta_id,
        empresa=request.user.empresa,
    )


def _serializar_proposta(proposta, incluir_historico=False):
    dados = {
        "id": proposta.id,
        "empresa_id": proposta.empresa_id,
        "cliente": {
            "id": proposta.cliente_id,
            "nome": proposta.cliente.nome,
        },
        "titulo": proposta.titulo,
        "descricao": proposta.descricao,
        "valor": str(proposta.valor),
        "desconto": str(proposta.desconto),
        "valor_final": str(proposta.valor_final),
        "valido_ate": proposta.valido_ate.isoformat() if proposta.valido_ate else None,
        "status": proposta.status,
        "contrato_id": proposta.contrato_id,
        "criado_por_id": proposta.criado_por_id,
        "criado_em": proposta.criado_em.isoformat(),
        "atualizado_em": proposta.atualizado_em.isoformat(),
    }

    if incluir_historico:
        dados["historico"] = [
            {
                "id": historico.id,
                "acao": historico.acao,
                "usuario_id": historico.usuario_id,
                "dados": historico.dados,
                "criado_em": historico.criado_em.isoformat(),
            }
            for historico in proposta.historicos.select_related("usuario")
        ]

    return dados


def _obter_json(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def _decimal(valor):
    return Decimal(str(valor))


def _data(valor):
    return date.fromisoformat(valor)
