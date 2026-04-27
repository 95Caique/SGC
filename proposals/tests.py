from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.management import call_command

from accounts.models import UsuarioCustomizado
from clients.models import Cliente
from companies.models import Empresa
from contracts.models import Contrato
from core.excecoes import ErroAcessoEmpresaNegado, ErroPropostaStatusInvalido
from proposals.models import Proposta, PropostaHistorico
from proposals.services import ServicoProposta


class PropostaBaseTestCase(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nome="Empresa Teste",
            cnpj="12.345.678/0001-90",
        )
        self.outra_empresa = Empresa.objects.create(
            nome="Outra Empresa",
            cnpj="98.765.432/0001-10",
        )
        self.usuario = UsuarioCustomizado.objects.create_user(
            username="admin",
            password="senha123",
            empresa=self.empresa,
            funcao=UsuarioCustomizado.Funcao.ADMINISTRADOR,
        )
        self.usuario_outra_empresa = UsuarioCustomizado.objects.create_user(
            username="outro",
            password="senha123",
            empresa=self.outra_empresa,
            funcao=UsuarioCustomizado.Funcao.ADMINISTRADOR,
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nome="Cliente Teste",
            tipo=Cliente.Tipo.PESSOA_JURIDICA,
        )
        self.cliente_outra_empresa = Cliente.objects.create(
            empresa=self.outra_empresa,
            nome="Cliente Outra Empresa",
            tipo=Cliente.Tipo.PESSOA_JURIDICA,
        )

    def criar_proposta(self, status=Proposta.Status.RASCUNHO):
        return ServicoProposta.criar_proposta(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Proposta de Servicos",
            descricao="Proposta mensal",
            valor=Decimal("1000.00"),
            desconto=Decimal("10.00"),
            valido_ate=timezone.localdate() + timedelta(days=15),
            criado_por=self.usuario,
            status=status,
        )


class CriacaoPropostaTestCase(PropostaBaseTestCase):
    def test_criar_proposta_calcula_valor_final(self):
        proposta = self.criar_proposta()

        self.assertEqual(proposta.valor_final, Decimal("900.00"))
        self.assertEqual(proposta.status, Proposta.Status.RASCUNHO)

    def test_criar_proposta_registra_historico(self):
        proposta = self.criar_proposta()

        historico = PropostaHistorico.objects.get(proposta=proposta)
        self.assertEqual(historico.acao, "criada")
        self.assertEqual(historico.dados["valor_final"]["new"], "900.00")

    def test_nao_cria_proposta_com_cliente_de_outra_empresa(self):
        with self.assertRaises(ErroAcessoEmpresaNegado):
            ServicoProposta.criar_proposta(
                empresa_id=self.empresa.id,
                cliente_id=self.cliente_outra_empresa.id,
                titulo="Proposta invalida",
                valor=Decimal("100.00"),
                criado_por=self.usuario,
            )


class EdicaoPropostaTestCase(PropostaBaseTestCase):
    def test_editar_desconto_registra_valor_final(self):
        proposta = self.criar_proposta()

        ServicoProposta.editar_proposta(
            proposta=proposta,
            usuario=self.usuario,
            desconto=Decimal("20.00"),
        )

        proposta.refresh_from_db()
        historico = proposta.historicos.filter(acao="editada").first()
        self.assertEqual(proposta.valor_final, Decimal("800.00"))
        self.assertIn("desconto", historico.dados)
        self.assertIn("valor_final", historico.dados)

    def test_usuario_nao_acessa_proposta_outra_empresa(self):
        proposta = self.criar_proposta()

        with self.assertRaises(ErroAcessoEmpresaNegado):
            ServicoProposta.editar_proposta(
                proposta=proposta,
                usuario=self.usuario_outra_empresa,
                titulo="Tentativa invalida",
            )


class ConversaoPropostaTestCase(PropostaBaseTestCase):
    def test_converter_proposta_aceita_em_contrato(self):
        proposta = self.criar_proposta(status=Proposta.Status.ACEITA)

        contrato = ServicoProposta.converter_em_contrato(
            proposta=proposta,
            usuario=self.usuario,
        )

        proposta.refresh_from_db()
        self.assertIsInstance(contrato, Contrato)
        self.assertEqual(contrato.valor_mensal, proposta.valor_final)
        self.assertEqual(contrato.status, Contrato.Status.ATIVO)
        self.assertEqual(proposta.status, Proposta.Status.CONVERTIDA)
        self.assertEqual(proposta.contrato, contrato)

    def test_nao_converter_proposta_nao_aceita(self):
        proposta = self.criar_proposta(status=Proposta.Status.ENVIADA)

        with self.assertRaises(ErroPropostaStatusInvalido):
            ServicoProposta.converter_em_contrato(
                proposta=proposta,
                usuario=self.usuario,
            )

    def test_contrato_fica_independente_apos_conversao(self):
        proposta = self.criar_proposta(status=Proposta.Status.ACEITA)
        contrato = ServicoProposta.converter_em_contrato(
            proposta=proposta,
            usuario=self.usuario,
        )

        ServicoProposta.editar_proposta(
            proposta=proposta,
            usuario=self.usuario,
            titulo="Proposta alterada depois",
            valor=Decimal("5000.00"),
        )

        contrato.refresh_from_db()
        self.assertEqual(contrato.titulo, "Proposta de Servicos")
        self.assertEqual(contrato.valor_mensal, Decimal("900.00"))


class LimpezaPropostaTestCase(PropostaBaseTestCase):
    def test_limpar_propostas_expiradas(self):
        proposta = ServicoProposta.criar_proposta(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Proposta vencida",
            valor=Decimal("1000.00"),
            valido_ate=timezone.localdate() - timedelta(days=1),
            criado_por=self.usuario,
            status=Proposta.Status.ENVIADA,
        )

        total = ServicoProposta.limpar_propostas_expiradas(usuario=self.usuario)

        proposta.refresh_from_db()
        self.assertEqual(total, 1)
        self.assertEqual(proposta.status, Proposta.Status.EXPIRADA)
        self.assertEqual(proposta.historicos.filter(acao="expirada").count(), 1)

    def test_limpeza_nao_expira_proposta_aceita(self):
        proposta = ServicoProposta.criar_proposta(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Proposta aceita vencida",
            valor=Decimal("1000.00"),
            valido_ate=timezone.localdate() - timedelta(days=1),
            criado_por=self.usuario,
            status=Proposta.Status.ACEITA,
        )

        total = ServicoProposta.limpar_propostas_expiradas(usuario=self.usuario)

        proposta.refresh_from_db()
        self.assertEqual(total, 0)
        self.assertEqual(proposta.status, Proposta.Status.ACEITA)

    def test_management_command_limpa_propostas_expiradas(self):
        proposta = ServicoProposta.criar_proposta(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Proposta vencida via comando",
            valor=Decimal("1000.00"),
            valido_ate=timezone.localdate() - timedelta(days=1),
            criado_por=self.usuario,
            status=Proposta.Status.RASCUNHO,
        )

        call_command("limpar_propostas_expiradas")

        proposta.refresh_from_db()
        self.assertEqual(proposta.status, Proposta.Status.EXPIRADA)


class ViewsPropostaTestCase(PropostaBaseTestCase):
    def test_listar_propostas_filtra_por_empresa_do_usuario(self):
        self.criar_proposta()
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("proposals:listar"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.json()["resultados"]), 1)
        self.assertEqual(resposta.json()["resultados"][0]["empresa_id"], self.empresa.id)

    def test_criar_proposta_via_view(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            reverse("proposals:criar"),
            data={
                "cliente_id": self.cliente.id,
                "titulo": "Proposta via view",
                "valor": "2000.00",
                "desconto": "5.00",
                "valido_ate": (timezone.localdate() + timedelta(days=10)).isoformat(),
            },
            content_type="application/json",
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["titulo"], "Proposta via view")
        self.assertEqual(resposta.json()["valor_final"], "1900.00")

    def test_detalhe_nao_expoe_proposta_de_outra_empresa(self):
        proposta = self.criar_proposta()
        self.client.force_login(self.usuario_outra_empresa)

        resposta = self.client.get(reverse("proposals:detalhe", args=[proposta.id]))

        self.assertEqual(resposta.status_code, 404)

    def test_alterar_status_via_view(self):
        proposta = self.criar_proposta()
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            reverse("proposals:alterar_status", args=[proposta.id]),
            data={"status": Proposta.Status.ENVIADA},
            content_type="application/json",
        )

        proposta.refresh_from_db()
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(proposta.status, Proposta.Status.ENVIADA)

    def test_converter_proposta_via_view(self):
        proposta = self.criar_proposta(status=Proposta.Status.ACEITA)
        self.client.force_login(self.usuario)

        resposta = self.client.post(reverse("proposals:converter", args=[proposta.id]))

        proposta.refresh_from_db()
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(proposta.status, Proposta.Status.CONVERTIDA)
        self.assertEqual(resposta.json()["contrato"]["status"], Contrato.Status.ATIVO)
