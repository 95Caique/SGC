from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
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


class ViewsPainelTestCase(ServicoPainelTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.usuario)

    def test_metricas_gerais_via_view(self):
        resposta = self.client.get(reverse("dashboard:metricas"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["total_contratos_ativos"], 1)
        self.assertEqual(resposta.json()["faturamento_mensal"], "1200.00")

    def test_contratos_proximos_vencimento_via_view(self):
        resposta = self.client.get(reverse("dashboard:contratos_vencimento"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.json()["resultados"]), 1)
        self.assertEqual(resposta.json()["resultados"][0]["titulo"], "Contrato ativo")

    def test_propostas_pendentes_via_view(self):
        resposta = self.client.get(reverse("dashboard:propostas_pendentes"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.json()["resultados"]), 1)
        self.assertEqual(resposta.json()["resultados"][0]["status"], Proposta.Status.RASCUNHO)

    def test_faturamento_por_cliente_via_view(self):
        resposta = self.client.get(reverse("dashboard:faturamento_clientes"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["resultados"][0]["nome"], "Cliente Teste")
        self.assertEqual(resposta.json()["resultados"][0]["faturamento_mensal"], "1200.00")

    def test_saude_via_view(self):
        resposta = self.client.get(reverse("dashboard:saude"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["contratos"]["total"], 2)
        self.assertEqual(resposta.json()["propostas"]["total"], 2)

    def test_administracao_renderiza_template_institucional(self):
        resposta = self.client.get(reverse("dashboard:administracao"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Modulos administrativos")
        self.assertContains(resposta, "data-table")

    def test_central_servicos_renderiza_template_institucional(self):
        resposta = self.client.get(reverse("dashboard:central_servicos"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Central de Servicos")
        self.assertContains(resposta, "data-table")

    def test_relatorios_renderiza_template_institucional(self):
        resposta = self.client.get(reverse("dashboard:relatorios"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Relatorios")
        self.assertContains(resposta, "data-table")
        self.assertContains(resposta, "Faturamento por cliente")
        self.assertContains(resposta, "Contratos proximos do vencimento")
        self.assertContains(resposta, "Propostas pendentes")
        self.assertContains(resposta, "Cliente Teste")
        self.assertContains(resposta, "Contrato ativo")
        self.assertContains(resposta, "Proposta rascunho")

    def test_interface_institucional_renderiza_tabelas(self):
        resposta = self.client.get(reverse("dashboard:interface"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Mostrando 2 Contratos")
        self.assertContains(resposta, "Mostrando 2 Propostas")
        self.assertContains(resposta, "total-row")

    def test_interface_institucional_sem_empresa_nao_quebra(self):
        usuario_sem_empresa = UsuarioCustomizado.objects.create_user(
            username="semempresa",
            password="senha123",
            funcao=UsuarioCustomizado.Funcao.ADMINISTRADOR,
        )
        self.client.force_login(usuario_sem_empresa)

        resposta = self.client.get(reverse("dashboard:interface"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Sem empresa")

    def test_superuser_sem_empresa_visualiza_painel_global(self):
        superusuario = UsuarioCustomizado.objects.create_superuser(
            username="super",
            password="senha123",
        )
        self.client.force_login(superusuario)

        resposta = self.client.get(reverse("dashboard:interface"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Mostrando 2 Contratos")
        self.assertContains(resposta, "Mostrando 2 Propostas")
        self.assertContains(resposta, "Acesso global")
        self.assertNotContains(resposta, "Vincule este usuario a uma empresa")

    def test_metricas_superuser_sem_empresa_considera_dados_globais(self):
        superusuario = UsuarioCustomizado.objects.create_superuser(
            username="super",
            password="senha123",
        )
        self.client.force_login(superusuario)

        resposta = self.client.get(reverse("dashboard:metricas"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["total_contratos_ativos"], 1)
        self.assertEqual(resposta.json()["total_clientes"], 1)
