from django.db import transaction
from django.utils import timezone

from contracts.models import Contrato
from contracts.services import ServicoContrato
from core.excecoes import ErroAcessoEmpresaNegado, ErroPermissao, ErroPropostaStatusInvalido, ErroValidacao
from core.permissoes import VerificadorPermissoes
from proposals.models import Proposta, PropostaHistorico


class ServicoProposta:
    CAMPOS_AUDITADOS = [
        "cliente",
        "titulo",
        "descricao",
        "valor",
        "desconto",
        "valor_final",
        "valido_ate",
        "status",
        "contrato",
    ]

    @classmethod
    @transaction.atomic
    def criar_proposta(
        cls,
        *,
        empresa_id,
        cliente_id,
        titulo,
        valor,
        criado_por,
        descricao="",
        desconto=0,
        valido_ate=None,
        status=Proposta.Status.RASCUNHO,
    ):
        if not VerificadorPermissoes.usuario_pode_criar(criado_por):
            raise ErroPermissao("Usuario nao possui permissao para criar propostas.")
        if (
            not VerificadorPermissoes.usuario_tem_acesso_global(criado_por)
            and criado_por.empresa_id != empresa_id
        ):
            raise ErroAcessoEmpresaNegado("Usuario nao pertence a empresa informada.")

        proposta = Proposta.objects.create(
            empresa_id=empresa_id,
            cliente_id=cliente_id,
            titulo=titulo,
            descricao=descricao,
            valor=valor,
            desconto=desconto,
            valido_ate=valido_ate,
            status=status,
            criado_por=criado_por,
        )

        if proposta.cliente.empresa_id != proposta.empresa_id:
            proposta.delete()
            raise ErroAcessoEmpresaNegado("Cliente nao pertence a empresa da proposta.")

        cls._registrar_historico(
            proposta=proposta,
            usuario=criado_por,
            acao="criada",
            dados={
                "titulo": {"old": None, "new": proposta.titulo},
                "status": {"old": None, "new": proposta.status},
                "valor_final": {"old": None, "new": str(proposta.valor_final)},
            },
        )
        return proposta

    @classmethod
    @transaction.atomic
    def editar_proposta(cls, *, proposta, usuario, **dados):
        cls._validar_acesso_edicao(proposta, usuario)

        alteracoes = {}
        valor_final_antigo = proposta.valor_final

        for campo, novo_valor in dados.items():
            if campo not in cls.CAMPOS_AUDITADOS or campo == "valor_final":
                continue

            valor_antigo = getattr(proposta, campo)
            if valor_antigo != novo_valor:
                alteracoes[campo] = {
                    "old": cls._serializar_valor(valor_antigo),
                    "new": cls._serializar_valor(novo_valor),
                }
                setattr(proposta, campo, novo_valor)

        if not alteracoes:
            return proposta

        if proposta.cliente.empresa_id != proposta.empresa_id:
            raise ErroAcessoEmpresaNegado("Cliente nao pertence a empresa da proposta.")

        proposta.valor_final = proposta.calcular_valor_final()
        if proposta.valor_final != valor_final_antigo:
            alteracoes["valor_final"] = {
                "old": cls._serializar_valor(valor_final_antigo),
                "new": cls._serializar_valor(proposta.valor_final),
            }

        proposta.save(update_fields=[*alteracoes.keys(), "atualizado_em"])
        cls._registrar_historico(
            proposta=proposta,
            usuario=usuario,
            acao="editada",
            dados=alteracoes,
        )
        return proposta

    @classmethod
    def marcar_como_enviada(cls, *, proposta, usuario):
        return cls._alterar_status(proposta=proposta, usuario=usuario, status=Proposta.Status.ENVIADA)

    @classmethod
    def aceitar_proposta(cls, *, proposta, usuario):
        return cls._alterar_status(proposta=proposta, usuario=usuario, status=Proposta.Status.ACEITA)

    @classmethod
    def rejeitar_proposta(cls, *, proposta, usuario):
        return cls._alterar_status(proposta=proposta, usuario=usuario, status=Proposta.Status.REJEITADA)

    @classmethod
    @transaction.atomic
    def converter_em_contrato(cls, *, proposta, usuario):
        cls._validar_acesso_edicao(proposta, usuario)
        proposta = Proposta.objects.select_for_update().get(pk=proposta.pk)

        if proposta.status != Proposta.Status.ACEITA:
            raise ErroPropostaStatusInvalido("Apenas propostas aceitas podem virar contrato.")
        if proposta.contrato_id:
            raise ErroPropostaStatusInvalido("Proposta ja foi convertida em contrato.")

        contrato = ServicoContrato.criar_contrato(
            empresa_id=proposta.empresa_id,
            cliente_id=proposta.cliente_id,
            titulo=proposta.titulo,
            descricao=proposta.descricao,
            valor_mensal=proposta.valor_final,
            data_inicio=timezone.localdate(),
            criado_por=usuario,
            status=Contrato.Status.ATIVO,
        )

        proposta.contrato = contrato
        proposta.status = Proposta.Status.CONVERTIDA
        proposta.save(update_fields=["contrato", "status", "atualizado_em"])
        cls._registrar_historico(
            proposta=proposta,
            usuario=usuario,
            acao="convertida",
            dados={
                "status": {"old": Proposta.Status.ACEITA, "new": Proposta.Status.CONVERTIDA},
                "contrato": {"old": None, "new": contrato.id},
            },
        )
        return contrato

    @classmethod
    @transaction.atomic
    def limpar_propostas_expiradas(cls, *, usuario=None, hoje=None):
        hoje = hoje or timezone.localdate()
        propostas = Proposta.objects.select_for_update().filter(
            status__in=[Proposta.Status.RASCUNHO, Proposta.Status.ENVIADA],
            valido_ate__lt=hoje,
        )

        total = 0
        for proposta in propostas:
            status_anterior = proposta.status
            proposta.status = Proposta.Status.EXPIRADA
            proposta.save(update_fields=["status", "atualizado_em"])
            cls._registrar_historico(
                proposta=proposta,
                usuario=usuario or proposta.criado_por,
                acao="expirada",
                dados={
                    "status": {
                        "old": status_anterior,
                        "new": Proposta.Status.EXPIRADA,
                    }
                },
            )
            total += 1

        return total

    @staticmethod
    def obter_historico_completo(proposta, usuario):
        if not VerificadorPermissoes.usuario_pode_acessar_recurso(usuario, proposta):
            raise ErroAcessoEmpresaNegado("Usuario nao pode acessar esta proposta.")
        return proposta.historicos.select_related("usuario").all()

    @classmethod
    def _alterar_status(cls, *, proposta, usuario, status):
        if status not in Proposta.Status.values:
            raise ErroValidacao("Status de proposta invalido.")
        return cls.editar_proposta(proposta=proposta, usuario=usuario, status=status)

    @classmethod
    def _validar_acesso_edicao(cls, proposta, usuario):
        if not VerificadorPermissoes.usuario_pode_editar(usuario):
            raise ErroPermissao("Usuario nao possui permissao para editar propostas.")
        if not VerificadorPermissoes.usuario_pode_acessar_recurso(usuario, proposta):
            raise ErroAcessoEmpresaNegado("Usuario nao pode acessar esta proposta.")

    @staticmethod
    def _registrar_historico(*, proposta, usuario, acao, dados):
        return PropostaHistorico.objects.create(
            proposta=proposta,
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
