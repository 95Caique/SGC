from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from clients.forms import ClienteForm, ContatoClienteForm
from clients.models import Cliente
from clients.services import ServicoCliente
from core.excecoes import ExcecaoContraflow
from core.permissoes import VerificadorPermissoes, requer_autenticacao, requer_criacao, requer_edicao


@requer_autenticacao
@require_GET
def listar_clientes(request):
    clientes = Cliente.objects.prefetch_related("contatos").order_by("nome")
    if not _usuario_tem_acesso_global(request.user):
        clientes = clientes.filter(empresa=request.user.empresa)
    clientes = _filtrar_clientes(clientes, request.GET)

    if _quer_json(request):
        return JsonResponse(
            {
                "resultados": [
                    _serializar_cliente(cliente)
                    for cliente in clientes
                ]
            }
        )

    clientes = list(clientes)
    return render(
        request,
        "clients/lista.html",
        {
            "clientes": clientes,
            "total_clientes": len(clientes),
            "filtros": request.GET,
            "tipo_choices": Cliente.Tipo.choices,
        },
    )


@requer_autenticacao
@require_GET
def detalhe_cliente(request, cliente_id):
    cliente = _obter_cliente(request, cliente_id)
    if _quer_json(request):
        return JsonResponse(_serializar_cliente(cliente))
    return render(
        request,
        "clients/detalhe.html",
        {
            "cliente": cliente,
            "contato_form": ContatoClienteForm(),
        },
    )


@requer_criacao
def criar_cliente(request):
    if request.method == "GET":
        return render(request, "clients/form.html", {"form": ClienteForm(usuario=request.user)})

    if _quer_json(request):
        dados = _obter_json(request)
        try:
            empresa_id = _empresa_id_para_cliente(request.user, dados)
            cliente = ServicoCliente.criar_cliente(
                empresa_id=empresa_id,
                nome=dados["nome"],
                email=dados.get("email", ""),
                tipo=dados["tipo"],
                criado_por=request.user,
            )
        except (KeyError, ExcecaoContraflow) as erro:
            return JsonResponse({"erro": str(erro)}, status=400)
        return JsonResponse(_serializar_cliente(cliente), status=201)

    form = ClienteForm(request.POST, usuario=request.user)
    if not form.is_valid():
        return render(request, "clients/form.html", {"form": form}, status=400)

    try:
        empresa_id = _empresa_id_para_cliente(request.user, form.cleaned_data)
        cliente = ServicoCliente.criar_cliente(
            empresa_id=empresa_id,
            nome=form.cleaned_data["nome"],
            email=form.cleaned_data["email"],
            tipo=form.cleaned_data["tipo"],
            criado_por=request.user,
        )
    except ExcecaoContraflow as erro:
        form.add_error(None, str(erro))
        return render(request, "clients/form.html", {"form": form}, status=400)

    return redirect("clients:detalhe", cliente_id=cliente.id)


@requer_edicao
def editar_cliente(request, cliente_id):
    cliente = _obter_cliente(request, cliente_id)
    if request.method == "GET":
        return render(
            request,
            "clients/form.html",
            {
                "form": ClienteForm(
                    usuario=request.user,
                    initial={
                        "nome": cliente.nome,
                        "email": cliente.email,
                        "tipo": cliente.tipo,
                        "empresa_id": cliente.empresa,
                    },
                ),
                "titulo_pagina": "Editar cliente",
                "breadcrumb_pagina": "Clientes › Editar",
                "texto_botao": "Atualizar",
            },
        )

    if _quer_json(request):
        dados = _obter_json(request)
        try:
            cliente = ServicoCliente.editar_cliente(
                cliente=cliente,
                usuario=request.user,
                nome=dados.get("nome"),
                email=dados.get("email"),
                tipo=dados.get("tipo"),
                empresa_id=dados.get("empresa_id"),
            )
        except ExcecaoContraflow as erro:
            return JsonResponse({"erro": str(erro)}, status=400)
        return JsonResponse(_serializar_cliente(cliente))

    form = ClienteForm(request.POST, usuario=request.user)
    if not form.is_valid():
        return render(
            request,
            "clients/form.html",
            {
                "form": form,
                "titulo_pagina": "Editar cliente",
                "breadcrumb_pagina": "Clientes › Editar",
                "texto_botao": "Atualizar",
            },
            status=400,
        )

    try:
        cliente = ServicoCliente.editar_cliente(
            cliente=cliente,
            usuario=request.user,
            nome=form.cleaned_data["nome"],
            email=form.cleaned_data["email"],
            tipo=form.cleaned_data["tipo"],
            empresa_id=_empresa_id_para_edicao_cliente(request.user, form.cleaned_data),
        )
    except ExcecaoContraflow as erro:
        form.add_error(None, str(erro))
        return render(
            request,
            "clients/form.html",
            {
                "form": form,
                "titulo_pagina": "Editar cliente",
                "breadcrumb_pagina": "Clientes › Editar",
                "texto_botao": "Atualizar",
            },
            status=400,
        )

    return redirect("clients:detalhe", cliente_id=cliente.id)


@requer_edicao
def criar_contato_cliente(request, cliente_id):
    cliente = _obter_cliente(request, cliente_id)
    if _quer_json(request):
        dados = _obter_json(request)
        try:
            contato = ServicoCliente.criar_contato(
                cliente=cliente,
                usuario=request.user,
                nome=dados["nome"],
                telefone=dados.get("telefone", ""),
                email=dados.get("email", ""),
            )
        except (KeyError, ExcecaoContraflow) as erro:
            return JsonResponse({"erro": str(erro)}, status=400)
        return JsonResponse(_serializar_contato(contato), status=201)

    form = ContatoClienteForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "clients/detalhe.html",
            {
                "cliente": cliente,
                "contato_form": form,
            },
            status=400,
        )

    try:
        ServicoCliente.criar_contato(
            cliente=cliente,
            usuario=request.user,
            nome=form.cleaned_data["nome"],
            telefone=form.cleaned_data["telefone"],
            email=form.cleaned_data["email"],
        )
    except ExcecaoContraflow as erro:
        form.add_error(None, str(erro))
        return render(
            request,
            "clients/detalhe.html",
            {
                "cliente": cliente,
                "contato_form": form,
            },
            status=400,
        )

    return redirect("clients:detalhe", cliente_id=cliente.id)


def _obter_cliente(request, cliente_id):
    clientes = Cliente.objects.prefetch_related("contatos", "contratos", "propostas")
    if not _usuario_tem_acesso_global(request.user):
        clientes = clientes.filter(empresa=request.user.empresa)
    return get_object_or_404(clientes, id=cliente_id)


def _serializar_cliente(cliente):
    return {
        "id": cliente.id,
        "empresa_id": cliente.empresa_id,
        "nome": cliente.nome,
        "email": cliente.email,
        "tipo": cliente.tipo,
        "contatos": [
            {
                "id": contato.id,
                "nome": contato.nome,
                "telefone": contato.telefone,
                "email": contato.email,
            }
            for contato in cliente.contatos.all()
        ],
    }


def _serializar_contato(contato):
    return {
        "id": contato.id,
        "cliente_id": contato.cliente_id,
        "nome": contato.nome,
        "telefone": contato.telefone,
        "email": contato.email,
    }


def _filtrar_clientes(clientes, parametros):
    texto = parametros.get("texto", "").strip()
    tipo = parametros.get("tipo", "").strip()
    email = parametros.get("email", "").strip()
    contato = parametros.get("contato", "").strip()

    if texto:
        clientes = clientes.filter(
            Q(nome__icontains=texto)
            | Q(email__icontains=texto)
            | Q(contatos__nome__icontains=texto)
        )
    if tipo:
        clientes = clientes.filter(tipo=tipo)
    if email:
        clientes = clientes.filter(email__icontains=email)
    if contato:
        clientes = clientes.filter(
            Q(contatos__nome__icontains=contato)
            | Q(contatos__email__icontains=contato)
            | Q(contatos__telefone__icontains=contato)
        )

    return clientes.distinct()


def _empresa_id_para_cliente(usuario, dados):
    if _usuario_tem_acesso_global(usuario):
        empresa = dados.get("empresa_id")
        return getattr(empresa, "id", empresa)
    return usuario.empresa_id


def _empresa_id_para_edicao_cliente(usuario, dados):
    if not _usuario_tem_acesso_global(usuario):
        return None
    empresa = dados.get("empresa_id")
    return getattr(empresa, "id", empresa)


def _usuario_tem_acesso_global(usuario):
    return VerificadorPermissoes.usuario_tem_acesso_global(usuario)


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


def _obter_json(request):
    import json

    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))
