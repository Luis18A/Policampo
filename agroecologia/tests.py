from django.test import TestCase, Client
from django.urls import reverse
from agroecologia.models import Diagnostico, Informe


class AgroecologiaViewsTestCase(TestCase):
    def setUp(self):
        # Ejecutar la carga de datos de prueba
        from django.core.management import call_command
        call_command('cargar_datos_prueba')
        self.client = Client()

    def test_diagnostico_view_status_code(self):
        response = self.client.get(reverse('diagnostico'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Diagnóstico Espacial y Déficit de Biodiversidad')
        self.assertContains(response, 'Finca La Candelaria')
        self.assertContains(response, 'Tomate Redondo')
        self.assertContains(response, 'Déficit de Biodiversidad')

    def test_informe_view_status_code(self):
        response = self.client.get(reverse('informe'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Informe Técnico de Rediseño')
        self.assertContains(response, 'INF-JUJ-2026-001')
        self.assertContains(response, 'Caléndula')
        self.assertContains(response, 'Borraja')
        self.assertContains(response, 'Vicia Villosa')
        self.assertContains(response, 'Calendario de Actividades Agroecológicas')

    def test_recalcular_diagnostico_post(self):
        diag = Diagnostico.objects.first()
        response = self.client.post(reverse('diagnostico'), {
            'finca_id': diag.finca.id_finca,
            'superficie_total': '12.0',
            'superficie_floral': '1.2',
        })
        self.assertEqual(response.status_code, 302)  # Redirección tras crear diagnóstico
