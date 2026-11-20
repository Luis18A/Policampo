from decimal import Decimal
from django import forms
from .models import (
    Establecimiento,
    Parcela,
    CroquisManual,
    COLORES_POLICAMPO,
    TIPOS_SECTOR,
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
        ]
        # [Unificación] Ya no se piden: cultivo principal, largo y ancho estimados ni
        # disponibilidad de agua. Los cultivos se cargan después, sector por sector.
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
    """
    Un sector del cuestionario. [Unificación] Solo se piden los datos del esquema del grupo:
    tipo (cultivo o sector de flores), nombre del cultivo, superficie y ubicación.
    El nombre del sector y el color se asignan solos en la vista.
    """
    tipo_uso = forms.ChoiceField(
        choices=TIPOS_SECTOR,
        label='Tipo de sector',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_uso'}),
    )

    class Meta:
        model = Parcela
        fields = [
            'tipo_uso',
            'cultivo',
            'superficie_ha',
            'ubicacion_relativa',
        ]
        widgets = {
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # En el cuestionario la superficie es obligatoria (en el croquis la calcula el dibujo)
        self.fields['superficie_ha'].required = True

    def clean_superficie_ha(self):
        val = self.cleaned_data.get('superficie_ha')
        if val is not None and val <= 0:
            raise forms.ValidationError("La superficie del sector debe ser mayor a cero.")
        return val

    def clean(self):
        cleaned_data = super().clean()
        tipo_uso = cleaned_data.get('tipo_uso')
        if tipo_uso == TipoUso.CULTIVO and not (cleaned_data.get('cultivo') or '').strip():
            self.add_error('cultivo', 'Indicá el nombre del cultivo.')
        if tipo_uso == TipoUso.FLORES:
            cleaned_data['cultivo'] = ''  # un sector de flores no lleva cultivo
        return cleaned_data
