from django import forms

from clients.models import Cliente


class PropostaForm(forms.Form):
    cliente_id = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),
        label="Cliente",
        empty_label="Selecione um cliente",
    )
    titulo = forms.CharField(label="Titulo", max_length=180)
    descricao = forms.CharField(label="Descricao", required=False, widget=forms.Textarea)
    valor = forms.DecimalField(label="Valor", max_digits=12, decimal_places=2)
    desconto = forms.DecimalField(label="Desconto", max_digits=5, decimal_places=2, initial=0)
    valido_ate = forms.DateField(
        label="Valido ate",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, empresa=None, escopo_global=False, **kwargs):
        super().__init__(*args, **kwargs)
        if escopo_global:
            self.fields["cliente_id"].queryset = Cliente.objects.select_related("empresa").order_by("nome")
        elif empresa:
            self.fields["cliente_id"].queryset = Cliente.objects.filter(empresa=empresa).order_by("nome")
