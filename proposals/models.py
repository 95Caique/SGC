from decimal import Decimal

from django.conf import settings
from django.db import models

from core.models import ModeloBase
from core.utils import UtilitariosValores


class Proposta(ModeloBase):
    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        ENVIADA = "enviada", "Enviada"
        ACEITA = "aceita", "Aceita"
        REJEITADA = "rejeitada", "Rejeitada"
        EXPIRADA = "expirada", "Expirada"
        CONVERTIDA = "convertida", "Convertida"

    empresa = models.ForeignKey(
        "companies.Empresa",
        on_delete=models.CASCADE,
        related_name="propostas",
    )
    cliente = models.ForeignKey(
        "clients.Cliente",
        on_delete=models.PROTECT,
        related_name="propostas",
    )
    titulo = models.CharField(max_length=180)
    descricao = models.TextField(blank=True)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    desconto = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    valor_final = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    valido_ate = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RASCUNHO,
    )
    contrato = models.OneToOneField(
        "contracts.Contrato",
        on_delete=models.SET_NULL,
        related_name="proposta_origem",
        null=True,
        blank=True,
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="propostas_criadas",
    )

    def calcular_valor_final(self):
        return UtilitariosValores.aplicar_desconto(self.valor, self.desconto)

    def save(self, *args, **kwargs):
        self.valor_final = self.calcular_valor_final()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Proposta"
        verbose_name_plural = "Propostas"


class PropostaHistorico(models.Model):
    proposta = models.ForeignKey(
        Proposta,
        on_delete=models.CASCADE,
        related_name="historicos",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="historicos_proposta",
    )
    acao = models.CharField(max_length=80)
    dados = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.proposta} - {self.acao}"

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Historico da proposta"
        verbose_name_plural = "Historicos das propostas"
