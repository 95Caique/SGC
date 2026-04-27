from datetime import timedelta
from decimal import Decimal
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import UsuarioCustomizado
from clients.models import Cliente
from companies.models import Empresa
from contracts.models import Contrato, ContratoHistorico
from contracts.services import ServicoContrato
from core.excecoes import ErroAcessoEmpresaNegado, ErroPermissao


class ContratoBaseTestCase(TestCase):
    def setUp(self):
        self.media_root_temporario = tempfile.mkdtemp()
        self.override_media = override_settings(MEDIA_ROOT=self.media_root_temporario)
        self.override_media.enable()
        self.addCleanup(self.override_media.disable)
        self.addCleanup(shutil.rmtree, self.media_root_temporario, ignore_errors=True)

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
        self.visualizador = UsuarioCustomizado.objects.create_user(
            username="viewer",
            password="senha123",
            empresa=self.empresa,
            funcao=UsuarioCustomizado.Funcao.VISUALIZADOR,
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
            email="cliente@example.com",
            tipo=Cliente.Tipo.PESSOA_JURIDICA,
        )
        self.cliente_outra_empresa = Cliente.objects.create(
            empresa=self.outra_empresa,
            nome="Cliente Outra Empresa",
            tipo=Cliente.Tipo.PESSOA_JURIDICA,
        )

    def criar_contrato(self):
        return ServicoContrato.criar_contrato(
            empresa_id=self.empresa.id,
            cliente_id=self.cliente.id,
            titulo="Contrato de Servicos",
            descricao="Contrato mensal",
            valor_mensal=Decimal("1500.00"),
            data_inicio=timezone.localdate(),
            data_fim=timezone.localdate() + timedelta(days=30),
            criado_por=self.usuario,
        )


class CriacaoContratoTestCase(ContratoBaseTestCase):
    def test_criar_contrato_com_sucesso(self):
        contrato = self.criar_contrato()

        self.assertEqual(contrato.empresa, self.empresa)
        self.assertEqual(contrato.cliente, self.cliente)
        self.assertEqual(contrato.status, Contrato.Status.ATIVO)

    def test_contrato_registra_historico(self):
        contrato = self.criar_contrato()

        historico = ContratoHistorico.objects.get(contrato=contrato)
        self.assertEqual(historico.acao, "criado")
        self.assertEqual(historico.dados["titulo"]["new"], contrato.titulo)

    def test_visualizador_nao_cria_contrato(self):
        with self.assertRaises(ErroPermissao):
            ServicoContrato.criar_contrato(
                empresa_id=self.empresa.id,
                cliente_id=self.cliente.id,
                titulo="Contrato bloqueado",
                valor_mensal=Decimal("100.00"),
                data_inicio=timezone.localdate(),
                criado_por=self.visualizador,
            )


class EdicaoContratoTestCase(ContratoBaseTestCase):
    def test_editar_contrato_registra_apenas_campos_alterados(self):
        contrato = self.criar_contrato()

        ServicoContrato.editar_contrato(
            contrato=contrato,
            usuario=self.usuario,
            titulo="Contrato atualizado",
            descricao=contrato.descricao,
        )

        contrato.refresh_from_db()
        historico = contrato.historicos.filter(acao="editado").first()
        self.assertEqual(contrato.titulo, "Contrato atualizado")
        self.assertEqual(list(historico.dados.keys()), ["titulo"])
        self.assertEqual(historico.dados["titulo"]["old"], "Contrato de Servicos")
        self.assertEqual(historico.dados["titulo"]["new"], "Contrato atualizado")

    def test_alterar_status_contrato(self):
        contrato = self.criar_contrato()

        ServicoContrato.alterar_status(
            contrato=contrato,
            usuario=self.usuario,
            status=Contrato.Status.SUSPENSO,
        )

        contrato.refresh_from_db()
        self.assertEqual(contrato.status, Contrato.Status.SUSPENSO)


class PermissoesContratoTestCase(ContratoBaseTestCase):
    def test_usuario_nao_acessa_contrato_outra_empresa(self):
        contrato = self.criar_contrato()

        with self.assertRaises(ErroAcessoEmpresaNegado):
            ServicoContrato.editar_contrato(
                contrato=contrato,
                usuario=self.usuario_outra_empresa,
                titulo="Tentativa invalida",
            )

    def test_nao_cria_contrato_com_cliente_de_outra_empresa(self):
        with self.assertRaises(ErroAcessoEmpresaNegado):
            ServicoContrato.criar_contrato(
                empresa_id=self.empresa.id,
                cliente_id=self.cliente_outra_empresa.id,
                titulo="Contrato invalido",
                valor_mensal=Decimal("100.00"),
                data_inicio=timezone.localdate(),
                criado_por=self.usuario,
            )


class ArquivoContratoTestCase(ContratoBaseTestCase):
    def test_adicionar_arquivo_incrementa_versao(self):
        contrato = self.criar_contrato()

        primeiro = ServicoContrato.adicionar_arquivo(
            contrato=contrato,
            arquivo=SimpleUploadedFile("contrato.pdf", b"arquivo 1"),
            usuario=self.usuario,
        )
        segundo = ServicoContrato.adicionar_arquivo(
            contrato=contrato,
            arquivo=SimpleUploadedFile("contrato.pdf", b"arquivo 2"),
            usuario=self.usuario,
        )

        self.assertEqual(primeiro.versao, 1)
        self.assertEqual(segundo.versao, 2)
        self.assertIn(f"empresa_{self.empresa.id}/contratos/{contrato.id}/v2.pdf", segundo.arquivo.name)


class ViewsContratoTestCase(ContratoBaseTestCase):
    def test_listar_contratos_filtra_por_empresa_do_usuario(self):
        self.criar_contrato()
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("contracts:listar"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.json()["resultados"]), 1)
        self.assertEqual(resposta.json()["resultados"][0]["empresa_id"], self.empresa.id)

    def test_criar_contrato_via_view(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            reverse("contracts:criar"),
            data={
                "cliente_id": self.cliente.id,
                "titulo": "Contrato via view",
                "valor_mensal": "2500.00",
                "data_inicio": timezone.localdate().isoformat(),
            },
            content_type="application/json",
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["titulo"], "Contrato via view")

    def test_detalhe_nao_expoe_contrato_de_outra_empresa(self):
        contrato = self.criar_contrato()
        self.client.force_login(self.usuario_outra_empresa)

        resposta = self.client.get(reverse("contracts:detalhe", args=[contrato.id]))

        self.assertEqual(resposta.status_code, 404)

    def test_alterar_status_via_view(self):
        contrato = self.criar_contrato()
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            reverse("contracts:alterar_status", args=[contrato.id]),
            data={"status": Contrato.Status.SUSPENSO},
            content_type="application/json",
        )

        contrato.refresh_from_db()
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(contrato.status, Contrato.Status.SUSPENSO)

    def test_upload_arquivo_via_view(self):
        contrato = self.criar_contrato()
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            reverse("contracts:upload_arquivo", args=[contrato.id]),
            data={"arquivo": SimpleUploadedFile("contrato.pdf", b"arquivo")},
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["versao"], 1)
