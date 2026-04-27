from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import UsuarioCustomizado
from clients.models import Cliente
from companies.models import Empresa
from companies.services import ServicoEmpresa
from contracts.models import Contrato
from contracts.services import ServicoContrato
from proposals.models import Proposta
from proposals.services import ServicoProposta


class ServicoEmpresaTestCase(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa Teste", cnpj="12.345.678/0001-90")
        self.outra_empresa = Empresa.objects.create(nome="Outra Empresa", cnpj="98.765.432/0001-10")
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
        self.cliente_outra_empresa = Cliente.objects.create(
            empresa=self.outra_empresa,
            nome="Cliente Outra",
            tipo=Cliente.Tipo.PESSOA_JURIDICA,
        )
        self.contrato = ServicoContrato.criar_contrato(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Contrato ativo",
            valor_mensal=Decimal("1200.00"),
            data_inicio=timezone.localdate(),
            data_fim=timezone.localdate() + timedelta(days=15),
            criado_por=self.usuario,
        )
        self.contrato_cancelado = ServicoContrato.criar_contrato(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Contrato cancelado",
            valor_mensal=Decimal("300.00"),
            data_inicio=timezone.localdate(),
            criado_por=self.usuario,
            status=Contrato.Status.CANCELADO,
        )
        ServicoProposta.criar_proposta(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Proposta enviada",
            valor=Decimal("500.00"),
            criado_por=self.usuario,
            status=Proposta.Status.ENVIADA,
        )

    def test_obter_dashboard_empresa(self):
        metricas = ServicoEmpresa.obter_dashboard_empresa(self.empresa)

        self.assertEqual(metricas["total_usuarios"], 1)
        self.assertEqual(metricas["total_clientes"], 1)
        self.assertEqual(metricas["total_contratos_ativos"], 1)
        self.assertEqual(metricas["faturamento_mensal"], Decimal("1200.00"))
        self.assertEqual(metricas["propostas_pendentes"], 1)

    def test_obter_faturamento_por_periodo(self):
        faturamento = ServicoEmpresa.obter_faturamento_por_periodo(
            self.empresa,
            data_inicio=timezone.localdate() - timedelta(days=1),
            data_fim=timezone.localdate() + timedelta(days=1),
        )

        self.assertEqual(faturamento, Decimal("1200.00"))

    def test_relatorio_clientes_por_valor(self):
        relatorio = list(ServicoEmpresa.relatorio_clientes_por_valor(self.empresa))

        self.assertEqual(relatorio[0]["nome"], "Cliente Teste")
        self.assertEqual(relatorio[0]["total_contratos"], 2)
        self.assertEqual(relatorio[0]["valor_total"], Decimal("1500.00"))


class ViewsEmpresaTestCase(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa Teste", cnpj="12.345.678/0001-90")
        self.usuario = UsuarioCustomizado.objects.create_user(
            username="adminempresa",
            password="senha123",
            empresa=self.empresa,
            funcao=UsuarioCustomizado.Funcao.ADMINISTRADOR,
        )

    def test_listar_empresas_renderiza_template_institucional(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("companies:listar"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Mostrando 1 Empresas")
        self.assertContains(resposta, "data-table")
