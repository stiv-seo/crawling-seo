from django.test import TestCase, Client
from django.urls import reverse
from .models import Analisis, Hallazgo, Imagen, Enlace

class AnalizadorTests(TestCase):
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
        self.analisis = Analisis.objects.create(
            url='https://ejemplo.com',
            codigo_estado=200,
            titulo='Ejemplo de Título',
            descripcion='Ejemplo de descripción',
            puntuacion=85
        )

    def test_inicio_view(self):
        """Probar la vista de inicio."""
        response = self.client.get(reverse('analizador:inicio'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analizador/inicio.html')

    def test_analizar_url_view(self):
        """Probar la vista de análisis de URL."""
        # Probar GET request
        response = self.client.get(reverse('analizador:analizar_url'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analizador/inicio.html')

        # Probar POST request con URL válida
        response = self.client.post(reverse('analizador:analizar_url'), {
            'url': 'https://ejemplo.com'
        })
        self.assertEqual(response.status_code, 302)  # Redirección después del análisis

        # Probar POST request con URL inválida
        response = self.client.post(reverse('analizador:analizar_url'), {
            'url': 'url-invalida'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'url', 'Enter a valid URL.')

    def test_detalle_analisis_view(self):
        """Probar la vista de detalle del análisis."""
        response = self.client.get(reverse('analizador:detalle_analisis', args=[self.analisis.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analizador/detalle_analisis.html')
        self.assertEqual(response.context['analisis'], self.analisis)

    def test_analisis_model(self):
        """Probar el modelo Analisis."""
        self.assertEqual(str(self.analisis), f"Análisis de {self.analisis.url} - {self.analisis.fecha_analisis}")
        self.assertEqual(self.analisis.url, 'https://ejemplo.com')
        self.assertEqual(self.analisis.codigo_estado, 200)
        self.assertEqual(self.analisis.puntuacion, 85)

    def test_hallazgo_model(self):
        """Probar el modelo Hallazgo."""
        hallazgo = Hallazgo.objects.create(
            analisis=self.analisis,
            tipo='error',
            mensaje='Ejemplo de hallazgo'
        )
        self.assertEqual(str(hallazgo), f"Error: {hallazgo.mensaje[:50]}...")
        self.assertEqual(hallazgo.analisis, self.analisis)
        self.assertEqual(hallazgo.tipo, 'error')

    def test_imagen_model(self):
        """Probar el modelo Imagen."""
        imagen = Imagen.objects.create(
            analisis=self.analisis,
            url='https://ejemplo.com/imagen.jpg',
            texto_alternativo='Ejemplo de imagen',
            formato='jpg'
        )
        self.assertEqual(str(imagen), f"Imagen: {imagen.url}")
        self.assertEqual(imagen.analisis, self.analisis)
        self.assertEqual(imagen.formato, 'jpg')

    def test_enlace_model(self):
        """Probar el modelo Enlace."""
        enlace = Enlace.objects.create(
            analisis=self.analisis,
            url='https://ejemplo.com/enlace',
            texto='Ejemplo de enlace'
        )
        self.assertEqual(str(enlace), f"Enlace: {enlace.texto or enlace.url}")
        self.assertEqual(enlace.analisis, self.analisis)
        self.assertEqual(enlace.texto, 'Ejemplo de enlace') 