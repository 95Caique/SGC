import os

from django.conf import settings
from django.db import models
from django.db.models import Max
from django.utils import timezone

from core.models import ModeloBase


class Contrato(ModeloBase):
    class Status(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        EXPIRADO = "expirado", "Expirado"
        CANCELADO = "cancelado", "Cancelado"
        SUSPENSO = "suspenso", "Suspenso"
        ENCERRADO = "encerrado", "Encerrado"

    empresa = models.ForeignKey(
        "companies.Empresa",
        on_delete=models.CASCADE,
        related_name="contratos",
    )
    cliente = models.ForeignKey(
        "clients.Cliente",
        on_delete=models.PROTECT,
        related_name="contratos",
    )
    titulo = models.CharField(max_length=180)
    descricao = models.TextField(blank=True)
    valor_mensal = models.DecimalField(max_digits=12, decimal_places=2)
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ATIVO,
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="contratos_criados",
    )

    def eh_ativo(self):
        return self.status == self.Status.ATIVO

    def eh_expirado(self):
        if self.status == self.Status.EXPIRADO:
            return True
        return bool(self.data_fim and self.data_fim < timezone.localdate())

    def dias_para_expiracao(self):
        if not self.data_fim:
            return None
        return (self.data_fim - timezone.localdate()).days

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"


def caminho_arquivo_contrato(instance, filename):
    extensao = os.path.splitext(filename)[1] or ".pdf"
    return (
        f"empresa_{instance.contrato.empresa_id}/"
        f"contratos/{instance.contrato_id}/"
        f"v{instance.versao}{extensao.lower()}"
    )


class ContratoArquivo(models.Model):
    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.CASCADE,
        related_name="arquivos",
    )
    arquivo = models.FileField(upload_to=caminho_arquivo_contrato)
    versao = models.PositiveIntegerField(editable=False)
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="arquivos_contrato_enviados",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.versao:
            ultima_versao = (
                ContratoArquivo.objects.filter(contrato=self.contrato)
                .aggregate(maior_versao=Max("versao"))
                .get("maior_versao")
                or 0
            )
            self.versao = ultima_versao + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.contrato} - v{self.versao}"

    class Meta:
        ordering = ["-versao"]
        verbose_name = "Arquivo do contrato"
        verbose_name_plural = "Arquivos dos contratos"
        constraints = [
            models.UniqueConstraint(
                fields=["contrato", "versao"],
                name="contrato_arquivo_versao_unica",
            )
        ]


class ContratoHistorico(models.Model):
    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.CASCADE,
        related_name="historicos",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="historicos_contrato",
    )
    acao = models.CharField(max_length=80)
    dados = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contrato} - {self.acao}"

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Historico do contrato"
        verbose_name_plural = "Historicos dos contratos"
