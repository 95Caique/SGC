from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import UsuarioCustomizado
from clients.models import Cliente
from companies.models import Empresa
from contracts.models import Contrato
from contracts.services import ServicoContrato
from dashboard.services import ServicoPainel
from proposals.models import Proposta
from proposals.services import ServicoProposta


class ServicoPainelTestCase(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa Teste", cnpj="12.345.678/0001-90")
        self.usuario = UsuarioCustomizado.objects.create_user(
            username="admin",
            password="senha123",
            empresa=self.empresa,
            funcao=UsuarioCustomizado.Funcao.ADMINISTRADOR,
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nome="Cliente Teste",
            tipo=Cliente.Tipo.PESSOA_JURIDICA,
        )
        ServicoContrato.criar_contrato(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Contrato ativo",
            valor_mensal=Decimal("1200.00"),
            data_inicio=timezone.localdate(),
            data_fim=timezone.localdate() + timedelta(days=10),
            criado_por=self.usuario,
            status=Contrato.Status.ATIVO,
        )
        ServicoContrato.criar_contrato(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Contrato suspenso",
            valor_mensal=Decimal("800.00"),
            data_inicio=timezone.localdate(),
            criado_por=self.usuario,
            status=Contrato.Status.SUSPENSO,
        )
        ServicoProposta.criar_proposta(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Proposta rascunho",
            valor=Decimal("500.00"),
            criado_por=self.usuario,
            status=Proposta.Status.RASCUNHO,
        )
        ServicoProposta.criar_proposta(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Proposta aceita",
            valor=Decimal("700.00"),
            criado_por=self.usuario,
            status=Proposta.Status.ACEITA,
        )

    def test_obter_metricas_gerais(self):
        metricas = ServicoPainel.obter_metricas_gerais(self.empresa)

        self.assertEqual(metricas["total_contratos_ativos"], 1)
        self.assertEqual(metricas["total_clientes"], 1)
        self.assertEqual(metricas["faturamento_mensal"], Decimal("1200.00"))
        self.assertEqual(metricas["propostas_pendentes"], 1)

    def test_obter_contratos_proximos_vencimento(self):
        contratos = list(ServicoPainel.obter_contratos_proximos_vencimento(self.empresa))

        self.assertEqual(len(contratos), 1)
        self.assertEqual(contratos[0].titulo, "Contrato ativo")

    def test_obter_saude_contratos(self):
        saude = ServicoPainel.obter_saude_contratos(self.empresa)

        self.assertEqual(saude["total"], 2)
        self.assertEqual(saude["ativos"], 1)
        self.assertEqual(saude["suspensos"], 1)

    def test_obter_saude_propostas(self):
        saude = ServicoPainel.obter_saude_propostas(self.empresa)

        self.assertEqual(saude["total"], 2)
        self.assertEqual(saude["rascunhos"], 1)
        self.assertEqual(saude["aceitas"], 1)
