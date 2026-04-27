from django.test import TestCase
from django.urls import reverse

from accounts.models import UsuarioCustomizado
from clients.models import Cliente, ContatoCliente
from companies.models import Empresa


class ViewsClienteTestCase(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nome="Empresa Teste",
            cnpj="12.345.678/0001-90",
        )
        self.usuario = UsuarioCustomizado.objects.create_user(
            username="admin",
            password="senha123",
            empresa=self.empresa,
            funcao=UsuarioCustomizado.Funcao.ADMINISTRADOR,
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nome="Cliente Teste",
            email="cliente@example.com",
            tipo=Cliente.Tipo.PESSOA_JURIDICA,
        )

    def test_listar_clientes_renderiza_template_institucional(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("clients:listar"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Mostrando 1 Clientes")
        self.assertContains(resposta, "data-table")

    def test_listar_clientes_json(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(f"{reverse('clients:listar')}?format=json")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["resultados"][0]["nome"], "Cliente Teste")

    def test_listar_clientes_filtra_por_texto_tipo_e_contato(self):
        ContatoCliente.objects.create(
            cliente=self.cliente,
            nome="Maria Operacoes",
            telefone="11999990000",
        )
        Cliente.objects.create(
            empresa=self.empresa,
            nome="Cliente Pessoa Fisica",
            email="pf@example.com",
            tipo=Cliente.Tipo.PESSOA_FISICA,
        )
        self.client.force_login(self.usuario)

        resposta = self.client.get(
            reverse("clients:listar"),
            {
                "texto": "Maria",
                "tipo": Cliente.Tipo.PESSOA_JURIDICA,
                "contato": "9999",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Mostrando 1 Clientes")
        self.assertContains(resposta, "Cliente Teste")
        self.assertNotContains(resposta, "Cliente Pessoa Fisica")

    def test_listar_clientes_json_aplica_filtros(self):
        Cliente.objects.create(
            empresa=self.empresa,
            nome="Cliente Avulso",
            email="avulso@example.com",
            tipo=Cliente.Tipo.PESSOA_JURIDICA,
        )
        self.client.force_login(self.usuario)

        resposta = self.client.get(
            reverse("clients:listar"),
            {"format": "json", "texto": "Avulso"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.json()["resultados"]), 1)
        self.assertEqual(resposta.json()["resultados"][0]["nome"], "Cliente Avulso")

    def test_superuser_sem_empresa_lista_clientes_globalmente(self):
        outra_empresa = Empresa.objects.create(
            nome="Outra Empresa",
            cnpj="98.765.432/0001-10",
        )
        Cliente.objects.create(
            empresa=outra_empresa,
            nome="Cliente Global",
            tipo=Cliente.Tipo.PESSOA_JURIDICA,
        )
        superusuario = UsuarioCustomizado.objects.create_superuser(
            username="super",
            password="senha123",
        )
        self.client.force_login(superusuario)

        resposta = self.client.get(reverse("clients:listar"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Mostrando 2 Clientes")
        self.assertContains(resposta, "Cliente Teste")
        self.assertContains(resposta, "Cliente Global")

    def test_detalhe_cliente_renderiza_template_institucional(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("clients:detalhe", args=[self.cliente.id]))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Dados do cliente")
        self.assertContains(resposta, "Cliente Teste")
        self.assertContains(resposta, "Adicionar contato")

    def test_criar_cliente_via_formulario_institucional(self):
        self.client.force_login(self.usuario)

        resposta_get = self.client.get(reverse("clients:criar"))
        self.assertEqual(resposta_get.status_code, 200)
        self.assertContains(resposta_get, "Novo cliente")

        resposta_post = self.client.post(
            reverse("clients:criar"),
            data={
                "nome": "Cliente formulario",
                "email": "formulario@example.com",
                "tipo": Cliente.Tipo.PESSOA_JURIDICA,
            },
        )

        cliente = Cliente.objects.get(nome="Cliente formulario")
        self.assertRedirects(resposta_post, reverse("clients:detalhe", args=[cliente.id]))

    def test_editar_cliente_via_formulario_institucional(self):
        self.client.force_login(self.usuario)

        resposta_get = self.client.get(reverse("clients:editar", args=[self.cliente.id]))
        self.assertEqual(resposta_get.status_code, 200)
        self.assertContains(resposta_get, "Editar cliente")

        resposta_post = self.client.post(
            reverse("clients:editar", args=[self.cliente.id]),
            data={
                "nome": "Cliente Atualizado",
                "email": "atualizado@example.com",
                "tipo": Cliente.Tipo.PESSOA_FISICA,
            },
        )

        self.cliente.refresh_from_db()
        self.assertRedirects(resposta_post, reverse("clients:detalhe", args=[self.cliente.id]))
        self.assertEqual(self.cliente.nome, "Cliente Atualizado")
        self.assertEqual(self.cliente.email, "atualizado@example.com")
        self.assertEqual(self.cliente.tipo, Cliente.Tipo.PESSOA_FISICA)

    def test_criar_contato_cliente_via_formulario_institucional(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            reverse("clients:criar_contato", args=[self.cliente.id]),
            data={
                "nome": "Contato Principal",
                "telefone": "11999990000",
                "email": "contato@example.com",
            },
        )

        contato = self.cliente.contatos.get(nome="Contato Principal")
        self.assertRedirects(resposta, reverse("clients:detalhe", args=[self.cliente.id]))
        self.assertEqual(contato.telefone, "11999990000")
        self.assertEqual(contato.email, "contato@example.com")

    def test_criar_contato_cliente_via_json(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            reverse("clients:criar_contato", args=[self.cliente.id]),
            data={
                "nome": "Contato API",
                "telefone": "11888880000",
                "email": "api@example.com",
            },
            content_type="application/json",
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["nome"], "Contato API")
        self.assertTrue(self.cliente.contatos.filter(nome="Contato API").exists())

    def test_usuario_nao_cria_contato_em_cliente_de_outra_empresa(self):
        outra_empresa = Empresa.objects.create(
            nome="Outra Empresa",
            cnpj="98.765.432/0001-10",
        )
        cliente_outra_empresa = Cliente.objects.create(
            empresa=outra_empresa,
            nome="Cliente Outra Empresa",
            tipo=Cliente.Tipo.PESSOA_JURIDICA,
        )
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            reverse("clients:criar_contato", args=[cliente_outra_empresa.id]),
            data={"nome": "Contato Bloqueado"},
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertFalse(cliente_outra_empresa.contatos.exists())
