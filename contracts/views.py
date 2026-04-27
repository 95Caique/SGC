import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from contracts.forms import ContratoForm
from contracts.models import Contrato
from contracts.services import ServicoContrato
from core.excecoes import ExcecaoContraflow
from core.permissoes import VerificadorPermissoes, requer_autenticacao, requer_criacao, requer_edicao


@requer_autenticacao
@require_GET
def listar_contratos(request):
    contratos = Contrato.objects.select_related("cliente", "criado_por").order_by("-criado_em")
    if not _usuario_tem_acesso_global(request.user):
        contratos = contratos.filter(empresa=request.user.empresa)
    contratos = _filtrar_contratos(contratos, request.GET)

    if _quer_json(request):
        return JsonResponse(
            {
                "resultados": [
                    _serializar_contrato(contrato)
                    for contrato in contratos
                ]
            }
        )

    contratos = list(contratos)
    return render(
        request,
        "contracts/lista.html",
        {
            "contratos": contratos,
            "total_contratos": len(contratos),
            "total_valor_contratos": sum(contrato.valor_mensal for contrato in contratos),
            "filtros": request.GET,
            "status_choices": Contrato.Status.choices,
        },
    )


@requer_criacao
def criar_contrato(request):
    if request.method == "GET":
        return render(
            request,
            "contracts/form.html",
            {
                "form": ContratoForm(
                    empresa=request.user.empresa,
                    escopo_global=_usuario_tem_acesso_global(request.user),
                )
            },
        )

    try:
        if _quer_json(request):
            dados = _obter_json(request)
        else:
            form = ContratoForm(
                request.POST,
                empresa=request.user.empresa,
                escopo_global=_usuario_tem_acesso_global(request.user),
            )
            if not form.is_valid():
                return render(request, "contracts/form.html", {"form": form}, status=400)
            dados = {
                **form.cleaned_data,
                "cliente_id": form.cleaned_data["cliente_id"].id,
            }
        empresa_id = _empresa_id_para_cliente(request.user, dados["cliente_id"])

        contrato = ServicoContrato.criar_contrato(
            empresa_id=empresa_id,
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

    if not _quer_json(request):
        return redirect("contracts:detalhe", contrato_id=contrato.id)
    return JsonResponse(_serializar_contrato(contrato), status=201)


@requer_autenticacao
@require_GET
def detalhe_contrato(request, contrato_id):
    contrato = _obter_contrato_da_empresa(request, contrato_id)
    if _quer_json(request):
        return JsonResponse(_serializar_contrato(contrato, incluir_historico=True))
    return render(
        request,
        "contracts/detalhe.html",
        {
            "contrato": contrato,
            "status_choices": Contrato.Status.choices,
            "arquivos": contrato.arquivos.select_related("enviado_por"),
        },
    )


@requer_edicao
def editar_contrato(request, contrato_id):
    contrato = _obter_contrato_da_empresa(request, contrato_id)
    if request.method == "GET":
        return render(
            request,
            "contracts/form.html",
            {
                "form": ContratoForm(
                    empresa=contrato.empresa,
                    initial={
                        "cliente_id": contrato.cliente,
                        "titulo": contrato.titulo,
                        "descricao": contrato.descricao,
                        "valor_mensal": contrato.valor_mensal,
                        "data_inicio": contrato.data_inicio,
                        "data_fim": contrato.data_fim,
                    },
                ),
                "titulo_pagina": "Editar contrato",
                "breadcrumb_pagina": "Contratos › Editar",
                "texto_botao": "Atualizar",
            },
        )

    try:
        if _quer_json(request):
            dados_edicao = _dados_contrato_json_para_edicao(_obter_json(request))
        else:
            form = ContratoForm(request.POST, empresa=contrato.empresa)
            if not form.is_valid():
                return render(
                    request,
                    "contracts/form.html",
                    {
                        "form": form,
                        "titulo_pagina": "Editar contrato",
                        "breadcrumb_pagina": "Contratos › Editar",
                        "texto_botao": "Atualizar",
                    },
                    status=400,
                )
            dados_edicao = {
                "cliente": form.cleaned_data["cliente_id"],
                "titulo": form.cleaned_data["titulo"],
                "descricao": form.cleaned_data["descricao"],
                "valor_mensal": form.cleaned_data["valor_mensal"],
                "data_inicio": form.cleaned_data["data_inicio"],
                "data_fim": form.cleaned_data["data_fim"],
            }

        contrato = ServicoContrato.editar_contrato(
            contrato=contrato,
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
            "contracts/form.html",
            {
                "form": form,
                "titulo_pagina": "Editar contrato",
                "breadcrumb_pagina": "Contratos › Editar",
                "texto_botao": "Atualizar",
            },
            status=400,
        )

    if _quer_json(request):
        return JsonResponse(_serializar_contrato(contrato))
    return redirect("contracts:detalhe", contrato_id=contrato.id)


@requer_edicao
@require_POST
def alterar_status_contrato(request, contrato_id):
    contrato = _obter_contrato_da_empresa(request, contrato_id)
    try:
        dados = _obter_dados_requisicao(request)
        contrato = ServicoContrato.alterar_status(
            contrato=contrato,
            usuario=request.user,
            status=dados["status"],
        )
    except KeyError as erro:
        return JsonResponse({"erro": f"Campo obrigatorio ausente: {erro}"}, status=400)
    except ExcecaoContraflow as erro:
        return JsonResponse({"erro": str(erro)}, status=400)

    if _quer_json(request):
        return JsonResponse(_serializar_contrato(contrato))
    return redirect("contracts:detalhe", contrato_id=contrato.id)


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

    if _quer_json(request):
        return JsonResponse(_serializar_arquivo_contrato(contrato_arquivo), status=201)
    return redirect("contracts:detalhe", contrato_id=contrato.id)


def _obter_contrato_da_empresa(request, contrato_id):
    if _usuario_tem_acesso_global(request.user):
        return get_object_or_404(
            Contrato.objects.select_related("cliente", "criado_por"),
            id=contrato_id,
        )
    if not request.user.empresa_id:
        raise Http404
    return get_object_or_404(
        Contrato.objects.select_related("cliente", "criado_por"),
        id=contrato_id,
        empresa=request.user.empresa,
    )


def _dados_contrato_json_para_edicao(dados):
    dados_edicao = {}
    if "cliente_id" in dados:
        from clients.models import Cliente

        dados_edicao["cliente"] = Cliente.objects.get(id=dados["cliente_id"])
    if "titulo" in dados:
        dados_edicao["titulo"] = dados["titulo"]
    if "descricao" in dados:
        dados_edicao["descricao"] = dados["descricao"]
    if "valor_mensal" in dados:
        dados_edicao["valor_mensal"] = _decimal(dados["valor_mensal"])
    if "data_inicio" in dados:
        dados_edicao["data_inicio"] = _data(dados["data_inicio"])
    if "data_fim" in dados:
        dados_edicao["data_fim"] = _data(dados["data_fim"]) if dados["data_fim"] else None
    return dados_edicao


def _empresa_id_para_cliente(usuario, cliente_id):
    if not _usuario_tem_acesso_global(usuario):
        return usuario.empresa_id
    from clients.models import Cliente

    return Cliente.objects.only("empresa_id").get(id=cliente_id).empresa_id


def _usuario_tem_acesso_global(usuario):
    return VerificadorPermissoes.usuario_tem_acesso_global(usuario)


def _filtrar_contratos(contratos, parametros):
    texto = parametros.get("texto", "").strip()
    cliente = parametros.get("cliente", "").strip()
    status = parametros.get("status", "").strip()
    data_inicio = parametros.get("data_inicio", "").strip()
    data_fim = parametros.get("data_fim", "").strip()

    if texto:
        contratos = contratos.filter(
            Q(titulo__icontains=texto)
            | Q(descricao__icontains=texto)
            | Q(cliente__nome__icontains=texto)
        )
    if cliente:
        contratos = contratos.filter(cliente__nome__icontains=cliente)
    if status:
        contratos = contratos.filter(status=status)
    if data_inicio:
        contratos = contratos.filter(data_inicio__gte=data_inicio)
    if data_fim:
        contratos = contratos.filter(data_fim__lte=data_fim)

    return contratos


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


def _serializar_arquivo_contrato(contrato_arquivo):
    return {
        "id": contrato_arquivo.id,
        "contrato_id": contrato_arquivo.contrato_id,
        "versao": contrato_arquivo.versao,
        "arquivo": contrato_arquivo.arquivo.name,
        "url": contrato_arquivo.arquivo.url if contrato_arquivo.arquivo else None,
        "enviado_por_id": contrato_arquivo.enviado_por_id,
        "criado_em": contrato_arquivo.criado_em.isoformat(),
    }


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
