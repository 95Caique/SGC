from django.db import transaction

from clients.models import Cliente, ContatoCliente
from core.excecoes import ErroAcessoEmpresaNegado, ErroPermissao
from core.permissoes import VerificadorPermissoes


class ServicoCliente:
    @staticmethod
    @transaction.atomic
    def criar_cliente(*, empresa_id, nome, tipo, criado_por, email=""):
        if not VerificadorPermissoes.usuario_pode_criar(criado_por):
            raise ErroPermissao("Usuario nao possui permissao para criar clientes.")
        if (
            not VerificadorPermissoes.usuario_tem_acesso_global(criado_por)
            and criado_por.empresa_id != empresa_id
        ):
            raise ErroAcessoEmpresaNegado("Usuario nao pertence a empresa informada.")

        return Cliente.objects.create(
            empresa_id=empresa_id,
            nome=nome,
            email=email,
            tipo=tipo,
        )

    @staticmethod
    @transaction.atomic
    def editar_cliente(*, cliente, usuario, nome=None, tipo=None, email=None, empresa_id=None):
        if not VerificadorPermissoes.usuario_pode_editar(usuario):
            raise ErroPermissao("Usuario nao possui permissao para editar clientes.")
        if not VerificadorPermissoes.usuario_pode_acessar_recurso(usuario, cliente):
            raise ErroAcessoEmpresaNegado("Usuario nao pode acessar este cliente.")

        if nome is not None:
            cliente.nome = nome
        if email is not None:
            cliente.email = email
        if tipo is not None:
            cliente.tipo = tipo
        if empresa_id is not None:
            if not VerificadorPermissoes.usuario_tem_acesso_global(usuario):
                raise ErroAcessoEmpresaNegado("Usuario nao pode alterar a empresa do cliente.")
            cliente.empresa_id = empresa_id

        cliente.save(update_fields=["nome", "email", "tipo", "empresa", "atualizado_em"])
        return cliente

    @staticmethod
    @transaction.atomic
    def criar_contato(*, cliente, usuario, nome, telefone="", email=""):
        if not VerificadorPermissoes.usuario_pode_editar(usuario):
            raise ErroPermissao("Usuario nao possui permissao para criar contatos.")
        if not VerificadorPermissoes.usuario_pode_acessar_recurso(usuario, cliente):
            raise ErroAcessoEmpresaNegado("Usuario nao pode acessar este cliente.")

        return ContatoCliente.objects.create(
            cliente=cliente,
            nome=nome,
            telefone=telefone,
            email=email,
        )
