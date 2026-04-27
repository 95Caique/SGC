from django import forms

from clients.models import Cliente
from companies.models import Empresa


class ClienteForm(forms.Form):
    nome = forms.CharField(label="Nome", max_length=150)
    email = forms.EmailField(label="Email", required=False)
    tipo = forms.ChoiceField(label="Tipo", choices=Cliente.Tipo.choices)
    empresa_id = forms.ModelChoiceField(
        queryset=Empresa.objects.none(),
        label="Empresa",
        required=False,
        empty_label="Selecione uma empresa",
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        if usuario and usuario.is_superuser:
            self.fields["empresa_id"].required = True
            self.fields["empresa_id"].queryset = Empresa.objects.order_by("nome")
        else:
            self.fields.pop("empresa_id")


class ContatoClienteForm(forms.Form):
    nome = forms.CharField(label="Nome", max_length=150)
    telefone = forms.CharField(label="Telefone", max_length=20, required=False)
    email = forms.EmailField(label="Email", required=False)
