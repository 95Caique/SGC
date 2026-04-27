import re
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.utils.text import slugify


class UtilitariosData:
    @staticmethod
    def obter_hoje():
        return timezone.localdate()

    @staticmethod
    def obter_agora():
        return timezone.now()

    @staticmethod
    def adicionar_dias(data, dias):
        return data + timedelta(days=dias)

    @staticmethod
    def diferenca_dias(data_inicial, data_final):
        return (data_final - data_inicial).days

    @staticmethod
    def eh_data_passada(data):
        return data < UtilitariosData.obter_hoje()

    @staticmethod
    def eh_data_proxima(data, dias=30):
        hoje = UtilitariosData.obter_hoje()
        return hoje <= data <= hoje + timedelta(days=dias)


class UtilitariosValores:
    @staticmethod
    def formatar_moeda(valor):
        return f"R$ {Decimal(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def calcular_percentual(valor, percentual):
        return ((Decimal(valor) * Decimal(percentual)) / Decimal("100")).quantize(Decimal("0.01"))

    @staticmethod
    def aplicar_desconto(valor, desconto):
        valor = Decimal(valor)
        return (valor - UtilitariosValores.calcular_percentual(valor, desconto)).quantize(Decimal("0.01"))


class UtilitariosString:
    @staticmethod
    def validar_email(email):
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))

    @staticmethod
    def validar_telefone(telefone):
        return bool(re.match(r"^\+?[0-9()\-\s]{8,20}$", telefone or ""))

    @staticmethod
    def validar_cpf(cpf):
        return len(re.sub(r"\D", "", cpf or "")) == 11

    @staticmethod
    def validar_cnpj(cnpj):
        return len(re.sub(r"\D", "", cnpj or "")) == 14

    @staticmethod
    def truncar_string(texto, limite=80):
        if not texto or len(texto) <= limite:
            return texto
        return f"{texto[:limite - 3]}..."

    @staticmethod
    def slugificar(texto):
        return slugify(texto)


class UtilitariosArquivo:
    @staticmethod
    def validar_tipo_arquivo(arquivo, tipos_permitidos):
        nome = getattr(arquivo, "name", "")
        return nome.lower().split(".")[-1] in tipos_permitidos

    @staticmethod
    def validar_tamanho_arquivo(arquivo, tamanho_maximo_mb):
        return arquivo.size <= tamanho_maximo_mb * 1024 * 1024

    @staticmethod
    def converter_bytes_para_mb(tamanho_bytes):
        return round(tamanho_bytes / (1024 * 1024), 2)
