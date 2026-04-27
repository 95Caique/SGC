import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from contracts.models import Contrato
from contracts.services import ServicoContrato
from core.excecoes import ExcecaoContraflow
from core.permissoes import requer_autenticacao, requer_criacao, requer_edicao


@requer_autenticacao
@require_GET
def listar_contratos(request):
    contratos = (
        Contrato.objects.filter(empresa=request.user.empresa)
        .select_related("cliente", "criado_por")
        .order_by("-criado_em")
    )
    status = request.GET.get("status")
    if status:
        contratos = contratos.filter(status=status)

    return JsonResponse(
        {
            "resultados": [
                _serializar_contrato(contrato)
                for contrato in contratos
            ]
        }
    )


@requer_criacao
@require_POST
def criar_contrato(request):
    try:
        dados = _obter_json(request)
        contrato = ServicoContrato.criar_contrato(
            empresa_id=request.user.empresa_id,
            cliente_id=dados["cliente_id"],
            titulo=dados["titulo"],
            descricao=dados.get("descricao", ""),
            valor_mensal=_decimal(dados["valor_mensal"]),
            data_inicio=_data(dados["data_inicio"]),
            data_fim=_data(dados["data_fim"]) if dados.get("data_fim") else None,
            criado_por=request.user,
        )
    except (KeyError, InvalidOperation, ValueError) as erro:
        return JsonResponse({"erro": f"Dados invalidos: {erro}"}, status=400)
    except ExcecaoContraflow as erro:
        return JsonResponse({"erro": str(erro)}, status=403)

    return JsonResponse(_serializar_contrato(contrato), status=201)


@requer_autenticacao
@require_GET
def detalhe_contrato(request, contrato_id):
    contrato = _obter_contrato_da_empresa(request, contrato_id)
    return JsonResponse(_serializar_contrato(contrato, incluir_historico=True))


@requer_edicao
@require_POST
def alterar_status_contrato(request, contrato_id):
    contrato = _obter_contrato_da_empresa(request, contrato_id)
    try:
        dados = _obter_json(request)
        contrato = ServicoContrato.alterar_status(
            contrato=contrato,
            usuario=request.user,
            status=dados["status"],
        )
    except KeyError as erro:
        return JsonResponse({"erro": f"Campo obrigatorio ausente: {erro}"}, status=400)
    except ExcecaoContraflow as erro:
        return JsonResponse({"erro": str(erro)}, status=400)

    return JsonResponse(_serializar_contrato(contrato))


@requer_edicao
@require_POST
def upload_arquivo_contrato(request, contrato_id):
    contrato = _obter_contrato_da_empresa(request, contrato_id)
    arquivo = request.FILES.get("arquivo")
    if not arquivo:
        return JsonResponse({"erro": "Arquivo nao informado."}, status=400)

    try:
        contrato_arquivo = ServicoContrato.adicionar_arquivo(
            contrato=contrato,
            arquivo=arquivo,
            usuario=request.user,
        )
    except ExcecaoContraflow as erro:
        return JsonResponse({"erro": str(erro)}, status=403)

    return JsonResponse(
        {
            "id": contrato_arquivo.id,
            "contrato_id": contrato.id,
            "versao": contrato_arquivo.versao,
            "arquivo": contrato_arquivo.arquivo.name,
            "criado_em": contrato_arquivo.criado_em.isoformat(),
        },
        status=201,
    )


def _obter_contrato_da_empresa(request, contrato_id):
    if not request.user.empresa_id:
        raise Http404
    return get_object_or_404(
        Contrato.objects.select_related("cliente", "criado_por"),
        id=contrato_id,
        empresa=request.user.empresa,
    )


def _serializar_contrato(contrato, incluir_historico=False):
    dados = {
        "id": contrato.id,
        "empresa_id": contrato.empresa_id,
        "cliente": {
            "id": contrato.cliente_id,
            "nome": contrato.cliente.nome,
        },
        "titulo": contrato.titulo,
        "descricao": contrato.descricao,
        "valor_mensal": str(contrato.valor_mensal),
        "data_inicio": contrato.data_inicio.isoformat(),
        "data_fim": contrato.data_fim.isoformat() if contrato.data_fim else None,
        "status": contrato.status,
        "criado_por_id": contrato.criado_por_id,
        "criado_em": contrato.criado_em.isoformat(),
        "atualizado_em": contrato.atualizado_em.isoformat(),
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
            for historico in contrato.historicos.select_related("usuario")
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
