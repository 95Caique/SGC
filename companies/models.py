from django.db import models

from core.models import ModeloBase


class Empresa(ModeloBase):
    nome = models.CharField(max_length=150)
    cnpj = models.CharField(max_length=18, unique=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)

    def total_usuarios(self):
        return self.usuarios.count()

    def total_clientes(self):
        return self.clientes.count()

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ["nome"]
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
