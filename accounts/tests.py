from django.test import TestCase
from django.urls import reverse

from accounts.models import UsuarioCustomizado
from companies.models import Empresa


class ViewsContaTestCase(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa Teste", cnpj="12.345.678/0001-90")
        self.usuario = UsuarioCustomizado.objects.create_user(
            username="adminconta",
            password="senha123",
            empresa=self.empresa,
            funcao=UsuarioCustomizado.Funcao.ADMINISTRADOR,
        )

    def test_gestao_pessoas_renderiza_template_institucional(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("accounts:gestao_pessoas"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Gestao de Pessoas")
        self.assertContains(resposta, "data-table")
