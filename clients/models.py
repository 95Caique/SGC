from django.db import models

from core.models import ModeloBase


class Cliente(ModeloBase):
    class Tipo(models.TextChoices):
        PESSOA_FISICA = "pf", "Pessoa fisica"
        PESSOA_JURIDICA = "pj", "Pessoa juridica"

    empresa = models.ForeignKey(
        "companies.Empresa",
        on_delete=models.CASCADE,
        related_name="clientes",
    )
    nome = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    tipo = models.CharField(max_length=2, choices=Tipo.choices)

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ["nome"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class ContatoCliente(ModeloBase):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="contatos",
    )
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.nome} - {self.cliente}"

    class Meta:
        ordering = ["nome"]
        verbose_name = "Contato do cliente"
        verbose_name_plural = "Contatos dos clientes"
