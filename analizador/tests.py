import os # For os.getenv mocking
from django.test import TestCase, Client
from django.urls import reverse
from .models import Analisis, Hallazgo, Imagen, Enlace
from .forms import AnalisisForm
from unittest.mock import patch, MagicMock, PropertyMock
from bs4 import BeautifulSoup
from .utils import obtener_recomendacion_ia, analizar_contenido_pagina, verificar_archivos_seo # Import the function to test
import google.generativeai as genai # To mock its exceptions

# Helper function to create a basic Analisis object for tests that need one
def crear_analisis_test(url="https://ejemplo.com", tecnologia="generic", scope="single_url", num_pages=None):
    return Analisis.objects.create(
        url=url,
        codigo_estado=200,
        titulo='Título de Prueba',
        descripcion='Descripción de Prueba',
        puntuacion=80,
        tecnologia_sitio=tecnologia,
        crawl_scope=scope,
        num_pages_solicitadas=num_pages
    )

class AnalisisFormTests(TestCase):
    def test_form_valid_single_url(self):
        """Test form is valid with single_url scope."""
        form_data = {
            'url': 'https://ejemplo.com',
            'crawl_scope': 'single_url',
            # num_pages not required
            'website_technology': 'wordpress'
        }
        form = AnalisisForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_multiple_pages(self):
        """Test form is valid with multiple_pages scope and num_pages."""
        form_data = {
            'url': 'https://ejemplo.com',
            'crawl_scope': 'multiple_pages',
            'num_pages': 5,
            'website_technology': 'django'
        }
        form = AnalisisForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_num_pages_required_for_multiple(self):
        """Test num_pages is required if crawl_scope is multiple_pages."""
        form_data = {
            'url': 'https://ejemplo.com',
            'crawl_scope': 'multiple_pages',
            # num_pages is missing
            'website_technology': 'generic'
        }
        form = AnalisisForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('num_pages', form.errors)
        self.assertEqual(form.errors['num_pages'][0], "This field is required when analysing multiple pages.")

    def test_form_num_pages_not_required_for_single(self):
        """Test num_pages is not required and cleared if crawl_scope is single_url."""
        form_data = {
            'url': 'https://ejemplo.com',
            'crawl_scope': 'single_url',
            'num_pages': 5, # Should be ignored and cleared
            'website_technology': 'generic'
        }
        form = AnalisisForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data.get('num_pages'))

    def test_form_num_pages_min_value(self):
        """Test num_pages minimum value is 1."""
        form_data = {
            'url': 'https://ejemplo.com',
            'crawl_scope': 'multiple_pages',
            'num_pages': 0, # Invalid
            'website_technology': 'generic'
        }
        form = AnalisisForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('num_pages', form.errors)
        # This error comes from the IntegerField's min_value validator before our custom clean()
        # self.assertEqual(form.errors['num_pages'][0], "The number of pages must be at least 1.")
        # Let's check the actual error message if it's different
        self.assertTrue("must be at least 1" in form.errors['num_pages'][0] or "Ensure this value is greater than or equal to 1" in form.errors['num_pages'][0])


    def test_form_num_pages_default_value(self):
        """Test num_pages has an initial (default) value of 10 in the form field."""
        form = AnalisisForm()
        self.assertEqual(form.fields['num_pages'].initial, 10)

    def test_form_website_technology_valid_choice(self):
        """Test website_technology accepts valid choices."""
        form_data = {
            'url': 'https://ejemplo.com',
            'crawl_scope': 'single_url',
            'website_technology': 'shopify' # Valid choice
        }
        form = AnalisisForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_website_technology_optional(self):
        """Test website_technology is optional."""
        form_data = {
            'url': 'https://ejemplo.com',
            'crawl_scope': 'single_url',
            # website_technology is missing
        }
        form = AnalisisForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('website_technology'), '') # Defaults to empty string if not provided

    def test_form_url_cleaning(self):
        """Test URL cleaning adds https if missing."""
        form_data = {'url': 'ejemplo.com', 'crawl_scope': 'single_url'}
        form = AnalisisForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['url'], 'https://ejemplo.com')

class AnalizadorViewsTests(TestCase): # Renamed from AnalizadorTests for clarity
    def setUp(self):
        """Configuración inicial para las pruebas de vistas."""
        self.client = Client()
        self.analisis_principal = crear_analisis_test() # Use helper

    def test_inicio_view_get(self):
        """Probar la vista de inicio (GET)."""
        response = self.client.get(reverse('analizador:inicio'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analizador/inicio.html')
        self.assertIsInstance(response.context['form'], AnalisisForm)

    # Test for POST to inicio view will be more complex due to mocking, added later

    def test_detalle_analisis_view(self):
        """Probar la vista de detalle del análisis."""
        response = self.client.get(reverse('analizador:detalle_analisis', args=[self.analisis_principal.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analizador/detalle_analisis.html')
        self.assertEqual(response.context['analisis'], self.analisis_principal)

    def test_resumen_analisis_view(self):
        """Probar la vista de resumen del análisis."""
        # Crear un análisis relacionado para probar el resumen con múltiples URLs
        Analisis.objects.create(
            url='https://ejemplo.com/pagina2',
            analisis_principal=self.analisis_principal,
            codigo_estado=200,
            titulo='Página 2',
            descripcion='Descripción Página 2',
            puntuacion=70
        )
        response = self.client.get(reverse('analizador:resumen_analisis', args=[self.analisis_principal.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analizador/resumen_analisis.html')
        self.assertEqual(response.context['analisis_principal'], self.analisis_principal)
        self.assertEqual(len(response.context['urls_analizadas']), 2) # Principal + 1 relacionada

class AnalizadorModelsTests(TestCase):
    def setUp(self):
        self.analisis = crear_analisis_test(
            url='https://modeltest.com',
            tecnologia='django',
            scope='multiple_pages',
            num_pages=5
        )

    def test_analisis_model_str(self):
        """Probar el método __str__ del modelo Analisis."""
        self.assertEqual(str(self.analisis), f"Análisis de https://modeltest.com - {self.analisis.fecha_analisis}")

    def test_analisis_model_fields(self):
        """Probar los campos del modelo Analisis."""
        self.assertEqual(self.analisis.url, 'https://modeltest.com')
        self.assertEqual(self.analisis.codigo_estado, 200)
        self.assertEqual(self.analisis.puntuacion, 80)
        self.assertEqual(self.analisis.tecnologia_sitio, 'django')
        self.assertEqual(self.analisis.crawl_scope, 'multiple_pages')
        self.assertEqual(self.analisis.num_pages_solicitadas, 5)


    def test_hallazgo_model(self):
        """Probar el modelo Hallazgo."""
        hallazgo = Hallazgo.objects.create(
            analisis=self.analisis,
            tipo='error',
            descripcion='Este es un error de prueba.' # Changed from 'mensaje'
        )
        self.assertEqual(str(hallazgo), f"Error: {hallazgo.descripcion[:50]}...")
        self.assertEqual(hallazgo.analisis, self.analisis)
        self.assertEqual(hallazgo.tipo, 'error')

    def test_imagen_model(self):
        """Probar el modelo Imagen."""
        imagen = Imagen.objects.create(
            analisis=self.analisis,
            url='https://modeltest.com/imagen.jpg',
            alt='Texto alternativo de prueba' # Changed from 'texto_alternativo'
        )
        self.assertEqual(str(imagen), f"Imagen: {imagen.url}")
        self.assertEqual(imagen.analisis, self.analisis)
        self.assertEqual(imagen.alt, 'Texto alternativo de prueba')
        # self.assertEqual(imagen.formato, 'jpg') # 'formato' field was removed

    def test_enlace_model(self):
        """Probar el modelo Enlace."""
        enlace = Enlace.objects.create(
            analisis=self.analisis,
            url='https://modeltest.com/enlace',
            texto='Texto de enlace de prueba',
            tipo='interno' # Added 'tipo'
        )
        # The __str__ method for Enlace was: f"{self.tipo}: {self.url}"
        self.assertEqual(str(enlace), f"interno: https://modeltest.com/enlace")
        self.assertEqual(enlace.analisis, self.analisis)
        self.assertEqual(enlace.texto, 'Texto de enlace de prueba')
        self.assertEqual(enlace.tipo, 'interno')

# Tests for utils.py functions will be added in a new class TestUtils

    @patch('analizador.views.requests.get')
    @patch('analizador.views.analizar_contenido_pagina')
    @patch('analizador.views.verificar_archivos_seo')
    @patch('analizador.views.obtener_urls_sitio')
    def test_inicio_view_post_single_url(self, mock_obtener_urls, mock_verificar_seo, mock_analizar_contenido, mock_requests_get):
        """Test POST to inicio view for a single URL analysis with mocking."""
        # Configure mocks
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.text = "<html><head><title>Test Page</title></head><body><h1>Hello</h1></body></html>"
        mock_requests_get.return_value = mock_response_get

        mock_analizar_contenido.return_value = {
            'titulo': 'Test Page',
            'descripcion_meta': 'Test description',
            'hallazgos_info': [{'tipo': 'info', 'descripcion': 'Test info finding'}],
            'imagenes_info': [],
            'enlaces_info': [],
            'h1_tags': ['Hello']
        }
        mock_verificar_seo.return_value = {
            'robots_txt_exists': True,
            'sitemap_xml_exists': False,
            'hallazgos_info': [{'tipo': 'warning', 'descripcion': 'Sitemap not found'}]
        }
        mock_obtener_urls.return_value = set() # No new URLs found/to be crawled for single_url

        form_data = {
            'url': 'https://testserver.com',
            'crawl_scope': 'single_url',
            'website_technology': 'django'
        }
        
        response = self.client.post(reverse('analizador:inicio'), form_data)

        self.assertEqual(response.status_code, 302) # Should redirect to resumen_analisis
        self.assertTrue(Analisis.objects.exists())
        analisis_obj = Analisis.objects.first()
        self.assertEqual(analisis_obj.url, 'https://testserver.com')
        self.assertEqual(analisis_obj.tecnologia_sitio, 'django')
        self.assertEqual(analisis_obj.crawl_scope, 'single_url')
        self.assertEqual(analisis_obj.num_pages_solicitadas, 1) # Default for single_url
        self.assertTrue(analisis_obj.robots_txt) # From mock_verificar_seo
        self.assertFalse(analisis_obj.sitemap_xml) # From mock_verificar_seo
        
        # Check that mocks were called
        mock_requests_get.assert_called_once_with('https://testserver.com', timeout=10)
        mock_analizar_contenido.assert_called_once()
        mock_verificar_seo.assert_called_once_with('https://testserver.com')
        mock_obtener_urls.assert_not_called() # Not called for single_url after the first page

        # Check Hallazgos created (1 from analizar_contenido, 1 from verificar_seo, 2 AI recommendations)
        self.assertEqual(Hallazgo.objects.filter(analisis=analisis_obj).count(), 2 * 2) # Original finding + AI rec for each
        self.assertEqual(Hallazgo.objects.filter(analisis=analisis_obj, tipo='recomendacion').count(), 2)


    @patch('analizador.views.requests.get')
    @patch('analizador.views.analizar_contenido_pagina')
    @patch('analizador.views.verificar_archivos_seo')
    @patch('analizador.views.obtener_urls_sitio')
    @patch('analizador.views.obtener_recomendacion_ia') # Mock AI recommendations
    def test_inicio_view_post_multiple_pages(self, mock_obtener_rec_ia, mock_obtener_urls, mock_verificar_seo, mock_analizar_contenido, mock_requests_get):
        """Test POST to inicio view for multiple pages with mocking."""
        # --- Configure Mocks ---
        # Mock requests.get to return different content for different URLs if needed
        def mock_get_requests_side_effect(url_actual, timeout):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            if url_actual == 'https://multipage.com':
                mock_resp.text = "<html><head><title>Main Page</title></head><body><a href='/page2'>Page 2</a><h1>Main</h1></body></html>"
            elif url_actual == 'https://multipage.com/page2':
                mock_resp.text = "<html><head><title>Page 2</title></head><body><h1>Subpage</h1></body></html>"
            else:
                mock_resp.text = "<html><head><title>Other Page</title></head><body><h1>Other</h1></body></html>"
            return mock_resp
        mock_requests_get.side_effect = mock_get_requests_side_effect

        # Mock analizar_contenido_pagina
        def mock_analizar_side_effect(soup, url_actual, website_technology):
            if url_actual == 'https://multipage.com':
                return {'titulo': 'Main Page', 'descripcion_meta': 'Desc main', 'hallazgos_info': [{'tipo':'error', 'descripcion':'Error main'}], 'imagenes_info': [], 'enlaces_info': [{'url':'/page2', 'texto':'Page 2', 'tipo':'interno'}], 'h1_tags':['Main']}
            elif url_actual == 'https://multipage.com/page2':
                 return {'titulo': 'Page 2', 'descripcion_meta': 'Desc page2', 'hallazgos_info': [], 'imagenes_info': [], 'enlaces_info': [], 'h1_tags':['Subpage']}
            return {'titulo': 'Other', 'descripcion_meta': 'Desc other', 'hallazgos_info': [], 'imagenes_info': [], 'enlaces_info': [], 'h1_tags':['Other']}
        mock_analizar_contenido.side_effect = mock_analizar_side_effect

        # Mock verificar_archivos_seo (only called for main URL)
        mock_verificar_seo.return_value = {'robots_txt_exists': True, 'sitemap_xml_exists': True, 'hallazgos_info': []}
        
        # Mock obtener_urls_sitio
        def mock_urls_side_effect(url_actual, soup, urls_visitadas_union):
            if url_actual == 'https://multipage.com':
                return {'https://multipage.com/page2'}
            return set()
        mock_obtener_urls.side_effect = mock_urls_side_effect

        # Mock AI recommendations
        mock_obtener_rec_ia.return_value = "AI Recommendation placeholder"

        # --- Form Data ---
        form_data = {
            'url': 'https://multipage.com',
            'crawl_scope': 'multiple_pages',
            'num_pages': 2, # Analyze main + 1 more
            'website_technology': 'generic'
        }

        # --- Make POST request ---
        response = self.client.post(reverse('analizador:inicio'), form_data)
        
        # --- Assertions ---
        self.assertEqual(response.status_code, 302) # Redirect to resumen
        self.assertEqual(Analisis.objects.count(), 2) # Main page + page2
        
        main_analisis = Analisis.objects.get(url='https://multipage.com')
        self.assertEqual(main_analisis.tecnologia_sitio, 'generic')
        self.assertEqual(main_analisis.crawl_scope, 'multiple_pages')
        self.assertEqual(main_analisis.num_pages_solicitadas, 2)
        self.assertTrue(main_analisis.robots_txt)
        self.assertTrue(main_analisis.sitemap_xml)

        # Check calls to mocks
        self.assertEqual(mock_requests_get.call_count, 2) # multipage.com and multipage.com/page2
        self.assertEqual(mock_analizar_contenido.call_count, 2)
        mock_verificar_seo.assert_called_once_with('https://multipage.com')
        mock_obtener_urls.assert_called_once() # Called for the first page

        # Check Hallazgos for the main page (1 original error + 1 AI rec)
        self.assertEqual(Hallazgo.objects.filter(analisis=main_analisis).count(), 1 * 2)
        self.assertEqual(Hallazgo.objects.filter(analisis=main_analisis, tipo='error').count(), 0) # Original error is not saved as 'error'
        self.assertEqual(Hallazgo.objects.filter(analisis=main_analisis, tipo='recomendacion').count(), 1 * 1) # One AI rec for the one finding

        page2_analisis = Analisis.objects.get(url='https://multipage.com/page2')
        self.assertEqual(Hallazgo.objects.filter(analisis=page2_analisis).count(), 0) # No findings for page 2 in mock setup


class AnalizadorUtilsTests(TestCase):
    def test_analizar_contenido_pagina_full_content(self):
        """Test analizar_contenido_pagina with typical content."""
        html_content = """
        <html>
            <head>
                <title>Página de Título Completo</title>
                <meta name="description" content="Esta es una meta descripción completa y detallada.">
            </head>
            <body>
                <h1>Encabezado H1 Principal</h1>
                <img src="/image.jpg" alt="Texto Alt de Imagen">
                <img src="/image2.png" alt="">
                <a href="/pagina-interna">Enlace Interno</a>
                <a href="https://externo.com">Enlace Externo</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        resultado = analizar_contenido_pagina(soup, "https://ejemplo.com/testpage")

        self.assertEqual(resultado['titulo'], "Página de Título Completo")
        self.assertEqual(resultado['descripcion_meta'], "Esta es una meta descripción completa y detallada.")
        self.assertIn({'tipo': 'info', 'descripcion': 'El título es demasiado largo. Se recomienda acortarlo a 50-60 caracteres.'}, resultado['hallazgos_info']) # Based on current logic
        self.assertIn({'tipo': 'info', 'descripcion': 'La meta descripción es demasiado larga. Se recomienda acortarla a 150-160 caracteres.'}, resultado['hallazgos_info']) # Based on current logic
        self.assertEqual(len(resultado['h1_tags']), 1)
        self.assertEqual(resultado['h1_tags'][0], "Encabezado H1 Principal")
        
        self.assertIn({'url': '/image.jpg', 'alt': 'Texto Alt de Imagen'}, resultado['imagenes_info'])
        self.assertIn({'url': '/image2.png', 'alt': ''}, resultado['imagenes_info'])
        self.assertTrue(any(h['descripcion'] == 'Imagen sin texto alternativo: /image2.png' for h in resultado['hallazgos_info']))
        
        self.assertIn({'url': '/pagina-interna', 'texto': 'Enlace Interno', 'tipo': 'interno'}, resultado['enlaces_info'])
        # Note: The obtener_enlaces util in utils.py doesn't make external links absolute if they start with http/https
        # It only makes relative links absolute. So, for "https://externo.com", it will remain as is.
        # The 'tipo' in enlaces_info is determined by comparing netloc, so it should be 'externo'.
        self.assertIn({'url': 'https://externo.com', 'texto': 'Enlace Externo', 'tipo': 'externo'}, resultado['enlaces_info'])
        # Check finding for few external links (current logic: <1 external link is an info)
        # Since we have 1 external link, this finding should not be present.
        self.assertFalse(any(h['descripcion'] == 'Pocos enlaces externos. Los enlaces a sitios autoritativos pueden mejorar el SEO.' for h in resultado['hallazgos_info']))


    def test_analizar_contenido_pagina_minimal_content(self):
        """Test analizar_contenido_pagina with minimal/missing content."""
        html_content = "<html><body></body></html>"
        soup = BeautifulSoup(html_content, 'html.parser')
        resultado = analizar_contenido_pagina(soup, "https://ejemplo.com/minimal")

        self.assertEqual(resultado['titulo'], "")
        self.assertEqual(resultado['descripcion_meta'], "")
        self.assertIn({'tipo': 'error', 'descripcion': 'La página no tiene título. El título es crucial para el SEO.'}, resultado['hallazgos_info'])
        self.assertIn({'tipo': 'error', 'descripcion': 'No se encontró meta descripción. Es importante para el SEO.'}, resultado['hallazgos_info'])
        self.assertEqual(len(resultado['h1_tags']), 0)
        self.assertIn({'tipo': 'error', 'descripcion': 'No se encontró encabezado H1. Cada página debe tener un H1.'}, resultado['hallazgos_info'])
        self.assertEqual(len(resultado['imagenes_info']), 0)
        self.assertEqual(len(resultado['enlaces_info']), 0)
        self.assertIn({'tipo': 'warning', 'descripcion': 'Pocos enlaces internos. Se recomienda más enlaces para mejorar la navegación.'}, resultado['hallazgos_info'])
        self.assertIn({'tipo': 'info', 'descripcion': 'Pocos enlaces externos. Los enlaces a sitios autoritativos pueden mejorar el SEO.'}, resultado['hallazgos_info'])


    @patch('analizador.utils.requests.get')
    def test_verificar_archivos_seo_both_exist(self, mock_get):
        """Test verificar_archivos_seo when both robots.txt and sitemap.xml exist."""
        mock_robots_response = MagicMock()
        mock_robots_response.status_code = 200
        mock_robots_response.text = "User-agent: *\nDisallow: /private/"
        
        mock_sitemap_response = MagicMock()
        mock_sitemap_response.status_code = 200
        mock_sitemap_response.text = "<xml></xml>"

        mock_get.side_effect = [mock_robots_response, mock_sitemap_response]
        
        resultado = verificar_archivos_seo("https://ejemplo.com")
        self.assertTrue(resultado['robots_txt_exists'])
        self.assertTrue(resultado['sitemap_xml_exists'])
        self.assertEqual(len(resultado['hallazgos_info']), 0)
        mock_get.assert_any_call("https://ejemplo.com/robots.txt", timeout=5)
        mock_get.assert_any_call("https://ejemplo.com/sitemap.xml", timeout=5)

    @patch('analizador.utils.requests.get')
    def test_verificar_archivos_seo_none_exist(self, mock_get):
        """Test verificar_archivos_seo when neither file exists."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        resultado = verificar_archivos_seo("https://ejemplo.com")
        self.assertFalse(resultado['robots_txt_exists'])
        self.assertFalse(resultado['sitemap_xml_exists'])
        self.assertIn({'tipo': 'info', 'descripcion': 'No se encontró archivo robots.txt o está vacío.'}, resultado['hallazgos_info'])
        self.assertIn({'tipo': 'info', 'descripcion': 'No se encontró archivo sitemap.xml o está vacío.'}, resultado['hallazgos_info'])

    @patch('analizador.utils.requests.get')
    def test_verificar_archivos_seo_request_exception(self, mock_get):
        """Test verificar_archivos_seo with requests.RequestException."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        resultado = verificar_archivos_seo("https://ejemplo.com")
        self.assertFalse(resultado['robots_txt_exists'])
        self.assertFalse(resultado['sitemap_xml_exists'])
        self.assertIn({'tipo': 'warning', 'descripcion': 'Error al intentar acceder a https://ejemplo.com/robots.txt.'}, resultado['hallazgos_info'])
        self.assertIn({'tipo': 'warning', 'descripcion': 'Error al intentar acceder a https://ejemplo.com/sitemap.xml.'}, resultado['hallazgos_info'])

    @patch('analizador.utils.os.getenv')
    def test_obtener_recomendacion_ia_no_api_key(self, mock_getenv):
        """Test obtener_recomendacion_ia returns error if GEMINI_API_KEY is not set."""
        mock_getenv.return_value = None
        resultado = obtener_recomendacion_ia("Test finding", "https://test.com", "generic", "info")
        self.assertEqual(resultado, "Error: AI recommendations are currently unavailable (API key not configured). Please consult standard SEO best practices.")

    @patch('analizador.utils.genai.configure')
    @patch('analizador.utils.genai.GenerativeModel')
    @patch('analizador.utils.os.getenv')
    def test_obtener_recomendacion_ia_api_key_configured_and_prompt(self, mock_getenv, mock_generative_model, mock_configure):
        """Test genai.configure is called and prompt is correct."""
        mock_getenv.return_value = "test_api_key"
        
        # Mock the model and its generate_content method
        mock_model_instance = MagicMock()
        mock_gemini_response = MagicMock()
        # Simulate response with 'parts'
        mock_part = MagicMock()
        mock_part.text = "Mocked AI Recommendation"
        type(mock_gemini_response).parts = PropertyMock(return_value=[mock_part])
        # Also mock .text as a fallback if parts logic changes or for different response structures
        type(mock_gemini_response).text = PropertyMock(return_value=None) # Ensure parts is used if available
        mock_model_instance.generate_content.return_value = mock_gemini_response
        mock_generative_model.return_value = mock_model_instance

        hallazgo_desc = "Título demasiado corto"
        url_pagina = "https://ejemplo.com/testpage"
        tecnologia = "wordpress"
        tipo_hallazgo = "warning"

        resultado = obtener_recomendacion_ia(hallazgo_desc, url_pagina, tecnologia, tipo_hallazgo)

        mock_getenv.assert_called_once_with("GEMINI_API_KEY")
        mock_configure.assert_called_once_with(api_key="test_api_key")
        mock_generative_model.assert_called_once_with('gemini-pro')
        
        # Check that generate_content was called
        mock_model_instance.generate_content.assert_called_once()
        # Get the actual prompt passed to generate_content
        actual_prompt = mock_model_instance.generate_content.call_args[0][0]
        
        self.assertIn(hallazgo_desc, actual_prompt)
        self.assertIn(url_pagina, actual_prompt)
        self.assertIn(tecnologia, actual_prompt)
        self.assertIn(tipo_hallazgo, actual_prompt)
        self.assertIn("As an expert SEO consultant", actual_prompt)
        self.assertEqual(resultado, "Mocked AI Recommendation")

    @patch('analizador.utils.os.getenv', return_value="fake_key") # API Key is present
    @patch('analizador.utils.genai.configure') # Mock configure
    @patch('analizador.utils.genai.GenerativeModel') # Mock GenerativeModel class
    def test_obtener_recomendacion_ia_successful_response_text_attribute(self, mock_generative_model, mock_configure, mock_getenv):
        """Test successful API response handling via the .text attribute."""
        mock_model_instance = MagicMock()
        mock_gemini_response = MagicMock()
        # Simulate response with direct .text attribute and empty/None parts
        type(mock_gemini_response).parts = PropertyMock(return_value=[]) # No parts with text
        type(mock_gemini_response).text = PropertyMock(return_value="Successful AI Response via text") # Text is directly available
        mock_model_instance.generate_content.return_value = mock_gemini_response
        mock_generative_model.return_value = mock_model_instance # mock_generative_model class returns our instance

        recommendation = obtener_recomendacion_ia("Test Desc", "https://test.com", "generic", "info")
        self.assertEqual(recommendation, "Successful AI Response via text")

    @patch('analizador.utils.os.getenv', return_value="fake_key")
    @patch('analizador.utils.genai.configure')
    @patch('analizador.utils.genai.GenerativeModel')
    def test_obtener_recomendacion_ia_empty_response(self, mock_generative_model, mock_configure, mock_getenv):
        """Test handling of empty or non-textual API response."""
        mock_model_instance = MagicMock()
        mock_gemini_response = MagicMock()
        type(mock_gemini_response).parts = PropertyMock(return_value=[]) # Empty parts
        type(mock_gemini_response).text = PropertyMock(return_value="")   # Empty text
        mock_model_instance.generate_content.return_value = mock_gemini_response
        mock_generative_model.return_value = mock_model_instance

        hallazgo_desc = "Vague issue"
        recommendation = obtener_recomendacion_ia(hallazgo_desc, "https://test.com", "generic", "info")
        expected_fallback = f"AI analysis complete, but no specific textual recommendation was generated for: {hallazgo_desc}. Please review standard SEO best practices for this type of issue (info)."
        self.assertEqual(recommendation, expected_fallback)


    @patch('analizador.utils.os.getenv', return_value="fake_key")
    @patch('analizador.utils.genai.configure')
    @patch('analizador.utils.genai.GenerativeModel')
    def test_obtener_recomendacion_ia_api_value_error(self, mock_generative_model, mock_configure, mock_getenv):
        """Test ValueError handling from Gemini API."""
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = ValueError("Content restriction error")
        mock_generative_model.return_value = mock_model_instance
        
        resultado = obtener_recomendacion_ia("Potentially problematic finding", "https://test.com", "generic", "error")
        self.assertEqual(resultado, "AI recommendation for 'Potentially problematic finding' could not be generated due to content restrictions or an internal API error. Please review manually.")

    @patch('analizador.utils.os.getenv', return_value="fake_key")
    @patch('analizador.utils.genai.configure')
    @patch('analizador.utils.genai.GenerativeModel')
    def test_obtener_recomendacion_ia_api_blocked_prompt_error(self, mock_generative_model, mock_configure, mock_getenv):
        """Test BlockedPromptException handling from Gemini API."""
        mock_model_instance = MagicMock()
        # Make sure the mocked exception type is correct, if it's genai.types.BlockedPromptException
        # we might need to mock that specific type if it's not a standard exception.
        # For now, assuming it's correctly imported as genai.types.BlockedPromptException in utils.py
        mock_model_instance.generate_content.side_effect = genai.types.BlockedPromptException("Prompt blocked")
        mock_generative_model.return_value = mock_model_instance
        
        resultado = obtener_recomendacion_ia("Blocked finding", "https://test.com", "generic", "error")
        self.assertEqual(resultado, "AI recommendation for 'Blocked finding' was blocked due to content safety policies. Please review the issue manually.")

    @patch('analizador.utils.os.getenv', return_value="fake_key")
    @patch('analizador.utils.genai.configure')
    @patch('analizador.utils.genai.GenerativeModel')
    def test_obtener_recomendacion_ia_api_stop_candidate_error(self, mock_generative_model, mock_configure, mock_getenv):
        """Test StopCandidateException handling from Gemini API."""
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = genai.types.generation_types.StopCandidateException("Stopped early")
        mock_generative_model.return_value = mock_model_instance
        
        resultado = obtener_recomendacion_ia("Complex finding", "https://test.com", "generic", "error")
        self.assertEqual(resultado, "AI recommendation generation for 'Complex finding' was stopped prematurely. The issue might be too complex or the response too long. Please review manually.")

    @patch('analizador.utils.os.getenv', return_value="fake_key")
    @patch('analizador.utils.genai.configure')
    @patch('analizador.utils.genai.GenerativeModel')
    def test_obtener_recomendacion_ia_generic_api_error(self, mock_generative_model, mock_configure, mock_getenv):
        """Test generic Exception handling from Gemini API."""
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = Exception("Unknown API error")
        mock_generative_model.return_value = mock_model_instance
        
        resultado = obtener_recomendacion_ia("Another finding", "https://test.com", "generic", "info")
        self.assertEqual(resultado, "AI recommendation could not be generated for 'Another finding'. An unexpected error occurred with the AI service.")