import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.excecoes import ExcecaoContraflow
from core.permissoes import VerificadorPermissoes, requer_autenticacao, requer_criacao, requer_edicao
from proposals.forms import PropostaForm
from proposals.models import Proposta
from proposals.services import ServicoProposta


@requer_autenticacao
@require_GET
def listar_propostas(request):
    propostas = Proposta.objects.select_related("cliente", "contrato", "criado_por").order_by("-criado_em")
    if not _usuario_tem_acesso_global(request.user):
        propostas = propostas.filter(empresa=request.user.empresa)
    propostas = _filtrar_propostas(propostas, request.GET)

    if _quer_json(request):
        return JsonResponse(
            {
                "resultados": [
                    _serializar_proposta(proposta)
                    for proposta in propostas
                ]
            }
        )

    propostas = list(propostas)
    return render(
        request,
        "proposals/lista.html",
        {
            "propostas": propostas,
            "total_propostas": len(propostas),
            "total_valor_propostas": sum(proposta.valor_final for proposta in propostas),
            "filtros": request.GET,
            "status_choices": Proposta.Status.choices,
        },
    )


@requer_criacao
def criar_proposta(request):
    if request.method == "GET":
        return render(
            request,
            "proposals/form.html",
            {
                "form": PropostaForm(
                    empresa=request.user.empresa,
                    escopo_global=_usuario_tem_acesso_global(request.user),
                )
            },
        )

    try:
        if _quer_json(request):
            dados = _obter_json(request)
        else:
            form = PropostaForm(
                request.POST,
                empresa=request.user.empresa,
                escopo_global=_usuario_tem_acesso_global(request.user),
            )
            if not form.is_valid():
                return render(request, "proposals/form.html", {"form": form}, status=400)
            dados = {
                **form.cleaned_data,
                "cliente_id": form.cleaned_data["cliente_id"].id,
            }
        empresa_id = _empresa_id_para_cliente(request.user, dados["cliente_id"])

        proposta = ServicoProposta.criar_proposta(
            empresa_id=empresa_id,
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

    if not _quer_json(request):
        return redirect("proposals:detalhe", proposta_id=proposta.id)
    return JsonResponse(_serializar_proposta(proposta), status=201)


@requer_autenticacao
@require_GET
def detalhe_proposta(request, proposta_id):
    proposta = _obter_proposta_da_empresa(request, proposta_id)
    if _quer_json(request):
        return JsonResponse(_serializar_proposta(proposta, incluir_historico=True))
    return render(
        request,
        "proposals/detalhe.html",
        {
            "proposta": proposta,
            "status_choices": Proposta.Status.choices,
        },
    )


@requer_edicao
def editar_proposta(request, proposta_id):
    proposta = _obter_proposta_da_empresa(request, proposta_id)
    if request.method == "GET":
        return render(
            request,
            "proposals/form.html",
            {
                "form": PropostaForm(
                    empresa=proposta.empresa,
                    initial={
                        "cliente_id": proposta.cliente,
                        "titulo": proposta.titulo,
                        "descricao": proposta.descricao,
                        "valor": proposta.valor,
                        "desconto": proposta.desconto,
                        "valido_ate": proposta.valido_ate,
                    },
                ),
                "titulo_pagina": "Editar proposta",
                "breadcrumb_pagina": "Propostas › Editar",
                "texto_botao": "Atualizar",
            },
        )

    try:
        if _quer_json(request):
            dados_edicao = _dados_proposta_json_para_edicao(_obter_json(request))
        else:
            form = PropostaForm(request.POST, empresa=proposta.empresa)
            if not form.is_valid():
                return render(
                    request,
                    "proposals/form.html",
                    {
                        "form": form,
                        "titulo_pagina": "Editar proposta",
                        "breadcrumb_pagina": "Propostas › Editar",
                        "texto_botao": "Atualizar",
                    },
                    status=400,
                )
            dados_edicao = {
                "cliente": form.cleaned_data["cliente_id"],
                "titulo": form.cleaned_data["titulo"],
                "descricao": form.cleaned_data["descricao"],
                "valor": form.cleaned_data["valor"],
                "desconto": form.cleaned_data["desconto"],
                "valido_ate": form.cleaned_data["valido_ate"],
            }

        proposta = ServicoProposta.editar_proposta(
            proposta=proposta,
            usuario=request.user,
            **dados_edicao,
        )
    except (InvalidOperation, ValueError) as erro:
        return JsonResponse({"erro": f"Dados invalidos: {erro}"}, status=400)
    except ExcecaoContraflow as erro:
        if _quer_json(request):
            return JsonResponse({"erro": str(erro)}, status=400)
        form.add_error(None, str(erro))
        return render(
            request,
            "proposals/form.html",
            {
                "form": form,
                "titulo_pagina": "Editar proposta",
                "breadcrumb_pagina": "Propostas › Editar",
                "texto_botao": "Atualizar",
            },
            status=400,
        )

    if _quer_json(request):
        return JsonResponse(_serializar_proposta(proposta))
    return redirect("proposals:detalhe", proposta_id=proposta.id)


@requer_edicao
@require_POST
def alterar_status_proposta(request, proposta_id):
    proposta = _obter_proposta_da_empresa(request, proposta_id)
    try:
        dados = _obter_dados_requisicao(request)
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

    if _quer_json(request):
        return JsonResponse(_serializar_proposta(proposta))
    return redirect("proposals:detalhe", proposta_id=proposta.id)


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
    if _eh_formulario_institucional(request):
        return redirect("contracts:detalhe", contrato_id=contrato.id)
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
    if _usuario_tem_acesso_global(request.user):
        return get_object_or_404(
            Proposta.objects.select_related("cliente", "contrato", "criado_por"),
            id=proposta_id,
        )
    if not request.user.empresa_id:
        raise Http404
    return get_object_or_404(
        Proposta.objects.select_related("cliente", "contrato", "criado_por"),
        id=proposta_id,
        empresa=request.user.empresa,
    )


def _dados_proposta_json_para_edicao(dados):
    dados_edicao = {}
    if "cliente_id" in dados:
        from clients.models import Cliente

        dados_edicao["cliente"] = Cliente.objects.get(id=dados["cliente_id"])
    if "titulo" in dados:
        dados_edicao["titulo"] = dados["titulo"]
    if "descricao" in dados:
        dados_edicao["descricao"] = dados["descricao"]
    if "valor" in dados:
        dados_edicao["valor"] = _decimal(dados["valor"])
    if "desconto" in dados:
        dados_edicao["desconto"] = _decimal(dados["desconto"])
    if "valido_ate" in dados:
        dados_edicao["valido_ate"] = _data(dados["valido_ate"]) if dados["valido_ate"] else None
    return dados_edicao


def _empresa_id_para_cliente(usuario, cliente_id):
    if not _usuario_tem_acesso_global(usuario):
        return usuario.empresa_id
    from clients.models import Cliente

    return Cliente.objects.only("empresa_id").get(id=cliente_id).empresa_id


def _usuario_tem_acesso_global(usuario):
    return VerificadorPermissoes.usuario_tem_acesso_global(usuario)


def _filtrar_propostas(propostas, parametros):
    texto = parametros.get("texto", "").strip()
    cliente = parametros.get("cliente", "").strip()
    status = parametros.get("status", "").strip()
    validade_inicio = parametros.get("validade_inicio", "").strip()
    validade_fim = parametros.get("validade_fim", "").strip()

    if texto:
        propostas = propostas.filter(
            Q(titulo__icontains=texto)
            | Q(descricao__icontains=texto)
            | Q(cliente__nome__icontains=texto)
        )
    if cliente:
        propostas = propostas.filter(cliente__nome__icontains=cliente)
    if status:
        propostas = propostas.filter(status=status)
    if validade_inicio:
        propostas = propostas.filter(valido_ate__gte=validade_inicio)
    if validade_fim:
        propostas = propostas.filter(valido_ate__lte=validade_fim)

    return propostas


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


def _obter_dados_requisicao(request):
    if _quer_json(request):
        return _obter_json(request)
    return request.POST


def _eh_formulario_institucional(request):
    return request.POST.get("interface") == "institucional"


def _decimal(valor):
    return Decimal(str(valor))


def _data(valor):
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(valor)


def _quer_json(request):
    if request.method != "GET":
        if request.POST:
            return False
        return (
            request.GET.get("format") == "json"
            or request.content_type == "application/json"
        )
    return (
        request.GET.get("format") == "json"
        or request.content_type == "application/json"
        or "application/json" in request.headers.get("Accept", "")
    )
