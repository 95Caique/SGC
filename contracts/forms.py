from django import forms

from clients.models import Cliente


class ContratoForm(forms.Form):
    cliente_id = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),
        label="Cliente",
        empty_label="Selecione um cliente",
    )
    titulo = forms.CharField(label="Titulo", max_length=180)
    descricao = forms.CharField(label="Descricao", required=False, widget=forms.Textarea)
    valor_mensal = forms.DecimalField(label="Valor mensal", max_digits=12, decimal_places=2)
    data_inicio = forms.DateField(label="Data de inicio", widget=forms.DateInput(attrs={"type": "date"}))
    data_fim = forms.DateField(
        label="Data de fim",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, empresa=None, escopo_global=False, **kwargs):
        super().__init__(*args, **kwargs)
        if escopo_global:
            self.fields["cliente_id"].queryset = Cliente.objects.select_related("empresa").order_by("nome")
        elif empresa:
            self.fields["cliente_id"].queryset = Cliente.objects.filter(empresa=empresa).order_by("nome")
