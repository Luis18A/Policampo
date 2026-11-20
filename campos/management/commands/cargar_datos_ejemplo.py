from decimal import Decimal
from django.core.management.base import BaseCommand
from campos.models import (
    COLORES_TIPO_USO,
    Establecimiento,
    Parcela,
    CroquisManual,
    DepartamentoJujuy,
    Ecorregion,
    TipoUso,
    UbicacionRelativa,
    MetodoCaracterizacion,
)


class Command(BaseCommand):
    help = ('Carga datos demostrativos agroecológicos de Jujuy para PoliCampo. '
            'Uso: python manage.py cargar_datos_ejemplo <nombre_de_usuario>')

    def add_arguments(self, parser):
        # [Integración] Los establecimientos tienen dueño: hay que decir a qué usuario cargarlos.
        parser.add_argument('usuario', help='Nombre de usuario (o email) que va a ser dueño de los datos de ejemplo')

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from django.core.management.base import CommandError
        from django.db.models import Q

        Usuario = get_user_model()
        identificador = options['usuario']
        usuario = Usuario.objects.filter(Q(username__iexact=identificador) | Q(email__iexact=identificador)).first()
        if usuario is None:
            raise CommandError(f'No existe el usuario "{identificador}". Creá la cuenta primero (registro o createsuperuser).')

        est, created = Establecimiento.objects.get_or_create(
            usuario=usuario,
            nombre="Finca Agroecológica Flor de Mayo",
            defaults={
                'direccion': 'Ruta Nacional 9 Km 1772, Paraje La Falda',
                'departamento': DepartamentoJujuy.TILCARA,
                'localidad': 'Maimará',
                'ecorregion': Ecorregion.QUEBRADA,
                'superficie_total_ha': Decimal('3.5000'),
                'cultivo_principal': 'Maíces andinos ancestrales y hortalizas',
                'metodo_caracterizacion': MetodoCaracterizacion.AMBOS,
            }
        )

        if not est.direccion:
            est.direccion = 'Ruta Nacional 9 Km 1772, Paraje La Falda'
            est.save(update_fields=['direccion'])

        if created or est.parcelas.count() == 0:
            self.stdout.write(self.style.SUCCESS(f'Configurando parcelas para "{est.nombre}"...'))

            # [Unificación] Solo cultivos y sectores de flores (esquema de datos del grupo).
            # El nombre se arma igual que en los formularios: el cultivo o "Sector de flores N".
            sectores = [
                # (tipo, cultivo, superficie, ubicación, origen, geometría en el croquis)
                (TipoUso.CULTIVO, 'Maíz morado', '1.2000', UbicacionRelativa.ARRIBA_IZQUIERDA,
                 'cuestionario', {'x': 50, 'y': 50, 'w': 220, 'h': 160}),
                (TipoUso.CULTIVO, 'Hortalizas de hoja', '0.6000', UbicacionRelativa.ARRIBA_CENTRO,
                 'cuestionario', {'x': 310, 'y': 50, 'w': 200, 'h': 160}),
                (TipoUso.CULTIVO, 'Haba', '0.8000', UbicacionRelativa.CENTRO,
                 'croquis_manual', {'x': 50, 'y': 240, 'w': 250, 'h': 160}),
                (TipoUso.FLORES, '', '0.7000', UbicacionRelativa.ABAJO_IZQUIERDA,
                 'croquis_manual', {'x': 330, 'y': 240, 'w': 180, 'h': 120}),
            ]
            numero_flores = 0
            for orden, (tipo, cultivo, superficie, ubicacion, origen, geometria) in enumerate(sectores, start=1):
                if tipo == TipoUso.FLORES:
                    numero_flores += 1
                Parcela.objects.create(
                    establecimiento=est,
                    nombre=Parcela.nombre_automatico(tipo, cultivo, numero_flores),
                    tipo_uso=tipo,
                    cultivo=cultivo,
                    superficie_ha=Decimal(superficie),
                    ubicacion_relativa=ubicacion,
                    color_hex=COLORES_TIPO_USO[tipo],
                    origen=origen,
                    geometria_visual=geometria,
                    orden=orden,
                )

            CroquisManual.objects.get_or_create(establecimiento=est)

            self.stdout.write(self.style.SUCCESS('¡Datos de ejemplo cargados y sincronizados exitosamente!'))
        else:
            self.stdout.write('El establecimiento ya cuenta con parcelas registradas.')
