from django.db.models import Count, Q, Sum
from django.utils import timezone

from clients.models import Cliente
from contracts.models import Contrato
from proposals.models import Proposta


class ServicoPainel:
    @staticmethod
    def obter_metricas_gerais(empresa):
        contratos_ativos = Contrato.objects.filter(status=Contrato.Status.ATIVO)
        propostas_pendentes = Proposta.objects.filter(
            status__in=[Proposta.Status.RASCUNHO, Proposta.Status.ENVIADA],
        )
        clientes = Cliente.objects.all()
        if empresa:
            contratos_ativos = contratos_ativos.filter(empresa=empresa)
            propostas_pendentes = propostas_pendentes.filter(empresa=empresa)
            clientes = clientes.filter(empresa=empresa)

        return {
            "total_contratos_ativos": contratos_ativos.count(),
            "total_clientes": clientes.count(),
            "faturamento_mensal": contratos_ativos.aggregate(total=Sum("valor_mensal"))["total"] or 0,
            "propostas_pendentes": propostas_pendentes.count(),
        }

    @staticmethod
    def obter_contratos_proximos_vencimento(empresa, dias=30):
        hoje = timezone.localdate()
        limite = hoje + timezone.timedelta(days=dias)
        contratos = Contrato.objects.filter(
            status=Contrato.Status.ATIVO,
            data_fim__range=(hoje, limite),
        )
        if empresa:
            contratos = contratos.filter(empresa=empresa)
        return contratos.select_related("cliente")

    @staticmethod
    def obter_propostas_pendentes(empresa):
        propostas = Proposta.objects.filter(
            status__in=[Proposta.Status.RASCUNHO, Proposta.Status.ENVIADA],
        )
        if empresa:
            propostas = propostas.filter(empresa=empresa)
        return propostas.select_related("cliente")

    @staticmethod
    def obter_faturamento_por_cliente(empresa):
        clientes = Cliente.objects.all()
        if empresa:
            clientes = clientes.filter(empresa=empresa)
        return (
            clientes.annotate(
                faturamento_mensal=Sum(
                    "contratos__valor_mensal",
                    filter=Q(contratos__status=Contrato.Status.ATIVO),
                ),
                contratos_ativos=Count(
                    "contratos",
                    filter=Q(contratos__status=Contrato.Status.ATIVO),
                ),
            )
            .order_by("-faturamento_mensal", "nome")
            .values("id", "nome", "faturamento_mensal", "contratos_ativos")
        )

    @staticmethod
    def obter_saude_contratos(empresa):
        contratos = Contrato.objects.all()
        if empresa:
            contratos = contratos.filter(empresa=empresa)
        total = contratos.count()
        por_status = dict(
            contratos.values_list("status").annotate(total=Count("id"))
        )

        return {
            "total": total,
            "ativos": por_status.get(Contrato.Status.ATIVO, 0),
            "expirados": por_status.get(Contrato.Status.EXPIRADO, 0),
            "cancelados": por_status.get(Contrato.Status.CANCELADO, 0),
            "suspensos": por_status.get(Contrato.Status.SUSPENSO, 0),
            "encerrados": por_status.get(Contrato.Status.ENCERRADO, 0),
        }

    @staticmethod
    def obter_saude_propostas(empresa):
        propostas = Proposta.objects.all()
        if empresa:
            propostas = propostas.filter(empresa=empresa)
        total = propostas.count()
        por_status = dict(
            propostas.values_list("status").annotate(total=Count("id"))
        )

        return {
            "total": total,
            "rascunhos": por_status.get(Proposta.Status.RASCUNHO, 0),
            "enviadas": por_status.get(Proposta.Status.ENVIADA, 0),
            "aceitas": por_status.get(Proposta.Status.ACEITA, 0),
            "rejeitadas": por_status.get(Proposta.Status.REJEITADA, 0),
            "expiradas": por_status.get(Proposta.Status.EXPIRADA, 0),
            "convertidas": por_status.get(Proposta.Status.CONVERTIDA, 0),
        }
