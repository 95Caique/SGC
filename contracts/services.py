from django.db import transaction

from contracts.models import Contrato, ContratoArquivo, ContratoHistorico
from core.excecoes import ErroAcessoEmpresaNegado, ErroPermissao, ErroValidacao
from core.permissoes import VerificadorPermissoes


class ServicoContrato:
    CAMPOS_AUDITADOS = [
        "cliente",
        "titulo",
        "descricao",
        "valor_mensal",
        "data_inicio",
        "data_fim",
        "status",
    ]

    @classmethod
    @transaction.atomic
    def criar_contrato(
        cls,
        *,
        empresa_id,
        cliente_id,
        titulo,
        valor_mensal,
        data_inicio,
        criado_por,
        descricao="",
        data_fim=None,
        status=Contrato.Status.ATIVO,
    ):
        if not VerificadorPermissoes.usuario_pode_criar(criado_por):
            raise ErroPermissao("Usuario nao possui permissao para criar contratos.")

        if criado_por.empresa_id != empresa_id:
            raise ErroAcessoEmpresaNegado("Usuario nao pertence a empresa informada.")

        contrato = Contrato.objects.create(
            empresa_id=empresa_id,
            cliente_id=cliente_id,
            titulo=titulo,
            descricao=descricao,
            valor_mensal=valor_mensal,
            data_inicio=data_inicio,
            data_fim=data_fim,
            status=status,
            criado_por=criado_por,
        )

        if contrato.cliente.empresa_id != contrato.empresa_id:
            contrato.delete()
            raise ErroAcessoEmpresaNegado("Cliente nao pertence a empresa do contrato.")

        cls._registrar_historico(
            contrato=contrato,
            usuario=criado_por,
            acao="criado",
            dados={
                "titulo": {"old": None, "new": contrato.titulo},
                "status": {"old": None, "new": contrato.status},
            },
        )
        return contrato

    @classmethod
    @transaction.atomic
    def editar_contrato(cls, *, contrato, usuario, **dados):
        cls._validar_acesso_edicao(contrato, usuario)

        alteracoes = {}
        for campo, novo_valor in dados.items():
            if campo not in cls.CAMPOS_AUDITADOS:
                continue

            valor_antigo = getattr(contrato, campo)
            if valor_antigo != novo_valor:
                alteracoes[campo] = {
                    "old": cls._serializar_valor(valor_antigo),
                    "new": cls._serializar_valor(novo_valor),
                }
                setattr(contrato, campo, novo_valor)

        if not alteracoes:
            return contrato

        if contrato.cliente.empresa_id != contrato.empresa_id:
            raise ErroAcessoEmpresaNegado("Cliente nao pertence a empresa do contrato.")

        contrato.save(update_fields=[*alteracoes.keys(), "atualizado_em"])
        cls._registrar_historico(
            contrato=contrato,
            usuario=usuario,
            acao="editado",
            dados=alteracoes,
        )
        return contrato

    @classmethod
    def alterar_status(cls, *, contrato, usuario, status):
        if status not in Contrato.Status.values:
            raise ErroValidacao("Status de contrato invalido.")
        return cls.editar_contrato(contrato=contrato, usuario=usuario, status=status)

    @classmethod
    @transaction.atomic
    def adicionar_arquivo(cls, *, contrato, arquivo, usuario):
        cls._validar_acesso_edicao(contrato, usuario)
        contrato_bloqueado = Contrato.objects.select_for_update().get(pk=contrato.pk)
        contrato_arquivo = ContratoArquivo.objects.create(
            contrato=contrato_bloqueado,
            arquivo=arquivo,
            enviado_por=usuario,
        )
        cls._registrar_historico(
            contrato=contrato_bloqueado,
            usuario=usuario,
            acao="arquivo_adicionado",
            dados={"versao": {"old": None, "new": contrato_arquivo.versao}},
        )
        return contrato_arquivo

    @staticmethod
    def obter_historico_completo(contrato, usuario):
        if not VerificadorPermissoes.usuario_pode_acessar_recurso(usuario, contrato):
            raise ErroAcessoEmpresaNegado("Usuario nao pode acessar este contrato.")
        return contrato.historicos.select_related("usuario").all()

    @classmethod
    def _validar_acesso_edicao(cls, contrato, usuario):
        if not VerificadorPermissoes.usuario_pode_editar(usuario):
            raise ErroPermissao("Usuario nao possui permissao para editar contratos.")
        if not VerificadorPermissoes.usuario_pode_acessar_recurso(usuario, contrato):
            raise ErroAcessoEmpresaNegado("Usuario nao pode acessar este contrato.")

    @staticmethod
    def _registrar_historico(*, contrato, usuario, acao, dados):
        return ContratoHistorico.objects.create(
            contrato=contrato,
            usuario=usuario,
            acao=acao,
            dados=dados,
        )

    @staticmethod
    def _serializar_valor(valor):
        if hasattr(valor, "pk"):
            return valor.pk
        if hasattr(valor, "isoformat"):
            return valor.isoformat()
        return str(valor) if valor is not None else None
