from decimal import Decimal
from django.core.management.base import BaseCommand
from campos.models import (
    Establecimiento,
    Parcela,
    CroquisManual,
    UbicacionGeografica,
    DepartamentoJujuy,
    Ecorregion,
    DisponibilidadAgua,
    TipoUso,
    UbicacionRelativa,
    MetodoCaracterizacion,
)


class Command(BaseCommand):
    help = 'Carga datos demostrativos agroecológicos de Jujuy para PoliCampo'

    def handle(self, *args, **options):
        est, created = Establecimiento.objects.get_or_create(
            nombre="Finca Agroecológica Flor de Mayo",
            defaults={
                'direccion': 'Ruta Nacional 9 Km 1772, Paraje La Falda',
                'departamento': DepartamentoJujuy.TILCARA,
                'localidad': 'Maimará',
                'ecorregion': Ecorregion.QUEBRADA,
                'superficie_total_ha': Decimal('3.5000'),
                'largo_estimado_m': Decimal('200.00'),
                'ancho_estimado_m': Decimal('175.00'),
                'disponibilidad_agua': DisponibilidadAgua.ACEQUIA,
                'cultivo_principal': 'Maíces andinos ancestrales y hortalizas',
                'metodo_caracterizacion': MetodoCaracterizacion.AMBOS,
            }
        )

        if not est.direccion:
            est.direccion = 'Ruta Nacional 9 Km 1772, Paraje La Falda'
            est.save(update_fields=['direccion'])

        if created or est.parcelas.count() == 0:
            self.stdout.write(self.style.SUCCESS(f'Configurando parcelas para "{est.nombre}"...'))

            # Parcela 1 (Cuestionario)
            Parcela.objects.create(
                establecimiento=est,
                nombre="Tablón de Maíces Andinos",
                tipo_uso=TipoUso.CULTIVO,
                cultivo="Maíz morado, capia y chulpi",
                superficie_ha=Decimal('1.2000'),
                ubicacion_relativa=UbicacionRelativa.ARRIBA_IZQUIERDA,
                color_hex='#2b8a3e',
                observaciones='Cultivo tradicional en terrazas con abono orgánico y compost.',
                origen='cuestionario',
                geometria_visual={'x': 50, 'y': 50, 'w': 220, 'h': 160},
                orden=1
            )

            # Parcela 2 (Cuestionario)
            Parcela.objects.create(
                establecimiento=est,
                nombre="Huerta Agroecológica Biointensiva",
                tipo_uso=TipoUso.CULTIVO,
                cultivo="Hortalizas de hoja, zanahoria y aromáticas",
                superficie_ha=Decimal('0.6000'),
                ubicacion_relativa=UbicacionRelativa.ARRIBA_CENTRO,
                color_hex='#20c997',
                observaciones='Riego por goteo con mulching vegetal y flores benéficas.',
                origen='cuestionario',
                geometria_visual={'x': 310, 'y': 50, 'w': 200, 'h': 160},
                orden=2
            )

            # Parcela 3 (Croquis Manual)
            Parcela.objects.create(
                establecimiento=est,
                nombre="Pastura de Alfalfa Criolla",
                tipo_uso=TipoUso.PASTURA,
                cultivo="Alfalfa criolla para animales",
                superficie_ha=Decimal('0.8000'),
                ubicacion_relativa=UbicacionRelativa.CENTRO,
                color_hex='#fcc419',
                observaciones='Rotación de pastoreo y cobertura de suelo.',
                origen='croquis_manual',
                geometria_visual={'x': 50, 'y': 240, 'w': 250, 'h': 160},
                orden=3
            )

            # Parcela 4 (Croquis Manual)
            Parcela.objects.create(
                establecimiento=est,
                nombre="Acequia y Reservorio Comunal",
                tipo_uso=TipoUso.AGUA,
                cultivo="",
                superficie_ha=Decimal('0.3000'),
                ubicacion_relativa=UbicacionRelativa.ABAJO_IZQUIERDA,
                color_hex='#339af0',
                observaciones='Turno de riego semanal.',
                origen='croquis_manual',
                geometria_visual={'x': 330, 'y': 240, 'w': 180, 'h': 120},
                orden=4
            )

            CroquisManual.objects.get_or_create(establecimiento=est)
            UbicacionGeografica.objects.get_or_create(
                establecimiento=est,
                defaults={
                    'latitud': Decimal('-23.6264'),
                    'longitud': Decimal('-65.3934'),
                    'zoom': 15,
                    'superficie_gis_ha': Decimal('3.4800'),
                }
            )

            self.stdout.write(self.style.SUCCESS('¡Datos de ejemplo cargados y sincronizados exitosamente!'))
        else:
            self.stdout.write('El establecimiento ya cuenta con parcelas registradas.')
