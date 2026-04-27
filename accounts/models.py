from django.contrib.auth.models import AbstractUser
from django.db import models


class UsuarioCustomizado(AbstractUser):
    class Funcao(models.TextChoices):
        ADMINISTRADOR = "administrador", "Administrador"
        GERENCIADOR = "gerenciador", "Gerenciador"
        VISUALIZADOR = "visualizador", "Visualizador"

    empresa = models.ForeignKey(
        "companies.Empresa",
        on_delete=models.PROTECT,
        related_name="usuarios",
        null=True,
        blank=True,
    )
    funcao = models.CharField(
        max_length=20,
        choices=Funcao.choices,
        default=Funcao.VISUALIZADOR,
    )

    def eh_administrador(self):
        return self.funcao == self.Funcao.ADMINISTRADOR

    def pode_editar(self):
        return self.funcao in [self.Funcao.ADMINISTRADOR, self.Funcao.GERENCIADOR]

    def pode_deletar(self):
        return self.eh_administrador()

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
