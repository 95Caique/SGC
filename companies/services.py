from django.db.models import Count, Sum

from contracts.models import Contrato
from proposals.models import Proposta


class ServicoEmpresa:
    @staticmethod
    def obter_dashboard_empresa(empresa):
        contratos_ativos = empresa.contratos.filter(status=Contrato.Status.ATIVO)
        propostas_pendentes = empresa.propostas.filter(
            status__in=[Proposta.Status.RASCUNHO, Proposta.Status.ENVIADA]
        )

        return {
            "total_usuarios": empresa.total_usuarios(),
            "total_clientes": empresa.total_clientes(),
            "total_contratos_ativos": contratos_ativos.count(),
            "faturamento_mensal": contratos_ativos.aggregate(total=Sum("valor_mensal"))["total"] or 0,
            "propostas_pendentes": propostas_pendentes.count(),
        }

    @staticmethod
    def obter_faturamento_por_periodo(empresa, data_inicio=None, data_fim=None):
        contratos = empresa.contratos.filter(status=Contrato.Status.ATIVO)

        if data_inicio:
            contratos = contratos.filter(data_inicio__gte=data_inicio)
        if data_fim:
            contratos = contratos.filter(data_inicio__lte=data_fim)

        return contratos.aggregate(total=Sum("valor_mensal"))["total"] or 0

    @staticmethod
    def relatorio_clientes_por_valor(empresa):
        return (
            empresa.clientes.annotate(
                total_contratos=Count("contratos"),
                valor_total=Sum("contratos__valor_mensal"),
            )
            .order_by("-valor_total", "nome")
            .values("id", "nome", "total_contratos", "valor_total")
        )
