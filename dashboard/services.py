from django.db.models import Count, Q, Sum
from django.utils import timezone

from contracts.models import Contrato
from proposals.models import Proposta


class ServicoPainel:
    @staticmethod
    def obter_metricas_gerais(empresa):
        contratos_ativos = Contrato.objects.filter(
            empresa=empresa,
            status=Contrato.Status.ATIVO,
        )
        propostas_pendentes = Proposta.objects.filter(
            empresa=empresa,
            status__in=[Proposta.Status.RASCUNHO, Proposta.Status.ENVIADA],
        )

        return {
            "total_contratos_ativos": contratos_ativos.count(),
            "total_clientes": empresa.clientes.count(),
            "faturamento_mensal": contratos_ativos.aggregate(total=Sum("valor_mensal"))["total"] or 0,
            "propostas_pendentes": propostas_pendentes.count(),
        }

    @staticmethod
    def obter_contratos_proximos_vencimento(empresa, dias=30):
        hoje = timezone.localdate()
        limite = hoje + timezone.timedelta(days=dias)
        return Contrato.objects.filter(
            empresa=empresa,
            status=Contrato.Status.ATIVO,
            data_fim__range=(hoje, limite),
        ).select_related("cliente")

    @staticmethod
    def obter_propostas_pendentes(empresa):
        return Proposta.objects.filter(
            empresa=empresa,
            status__in=[Proposta.Status.RASCUNHO, Proposta.Status.ENVIADA],
        ).select_related("cliente")

    @staticmethod
    def obter_faturamento_por_cliente(empresa):
        return (
            empresa.clientes.annotate(
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
        total = Contrato.objects.filter(empresa=empresa).count()
        por_status = dict(
            Contrato.objects.filter(empresa=empresa)
            .values_list("status")
            .annotate(total=Count("id"))
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
        total = Proposta.objects.filter(empresa=empresa).count()
        por_status = dict(
            Proposta.objects.filter(empresa=empresa)
            .values_list("status")
            .annotate(total=Count("id"))
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
