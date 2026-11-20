from decimal import Decimal
from django import forms
from .models import (
    Establecimiento,
    Parcela,
    CroquisManual,
    COLORES_POLICAMPO,
    TipoUso,
    UbicacionRelativa,
    DepartamentoJujuy,
    Ecorregion,
    DisponibilidadAgua,
)


class EstablecimientoForm(forms.ModelForm):
    class Meta:
        model = Establecimiento
        fields = [
            'nombre',
            'direccion',
            'departamento',
            'localidad',
            'ecorregion',
            'superficie_total_ha',
            'largo_estimado_m',
            'ancho_estimado_m',
            'disponibilidad_agua',
            'cultivo_principal',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej. Finca La Huerta Agroecológica',
                'autocomplete': 'off',
                'required': True,
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej. Ruta Nacional 9 Km 1772, Paraje La Falda...',
                'autocomplete': 'off',
            }),
            'departamento': forms.Select(attrs={
                'class': 'form-select',
            }),
            'localidad': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej. Maimará, Tilcara, Perico...',
                'autocomplete': 'off',
                'required': True,
            }),
            'ecorregion': forms.Select(attrs={
                'class': 'form-select',
            }),
            'superficie_total_ha': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej. 2.5',
                'step': '0.0001',
                'min': '0.0001',
                'required': True,
            }),
            'largo_estimado_m': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Opcional (metros)',
                'step': '0.1',
                'min': '1',
            }),
            'ancho_estimado_m': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Opcional (metros)',
                'step': '0.1',
                'min': '1',
            }),
            'disponibilidad_agua': forms.Select(attrs={
                'class': 'form-select',
            }),
            'cultivo_principal': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej. Maíz andino, hortalizas de hoja, papa oca...',
                'autocomplete': 'off',
                'required': True,
            }),
        }
        help_texts = {
            'direccion': 'Permite ubicar el predio en el territorio (no inventa la distribución interna de cultivos).',
            'superficie_total_ha': 'Superficie total en hectáreas (1 ha = 10.000 m²).',
        }

    def clean_superficie_total_ha(self):
        val = self.cleaned_data.get('superficie_total_ha')
        if val is None or val <= 0:
            raise forms.ValidationError("La superficie total debe ser mayor a 0 hectáreas.")
        return val


class ParcelaForm(forms.ModelForm):
    class Meta:
        model = Parcela
        fields = [
            'nombre',
            'tipo_uso',
            'cultivo',
            'superficie_ha',
            'ubicacion_relativa',
            'color_hex',
            'observaciones',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej. Parcela Norte / Tablón 1 / Huerta',
                'required': True,
            }),
            'tipo_uso': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_tipo_uso',
            }),
            'cultivo': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej. Maíz morado, habas, lechuga...',
                'id': 'id_cultivo',
            }),
            'superficie_ha': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej. 0.50',
                'step': '0.0001',
                'min': '0.0001',
                'required': True,
                'id': 'id_superficie_ha',
            }),
            'ubicacion_relativa': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_ubicacion_relativa',
            }),
            'color_hex': forms.HiddenInput(attrs={
                'id': 'id_color_hex',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Detalles adicionales, pendiente, sombra, riego...',
                'rows': 2,
            }),
        }

    def clean_superficie_ha(self):
        val = self.cleaned_data.get('superficie_ha')
        if val is not None and val <= 0:
            raise forms.ValidationError("La superficie de la parcela debe ser mayor a cero.")
        return val

    def clean(self):
        cleaned_data = super().clean()
        tipo_uso = cleaned_data.get('tipo_uso')
        cultivo = cleaned_data.get('cultivo')
        if tipo_uso in [TipoUso.CULTIVO, TipoUso.PASTURA] and not cultivo:
            self.add_error('cultivo', 'Indicá el nombre del cultivo o especie sembrada.')
        return cleaned_data
