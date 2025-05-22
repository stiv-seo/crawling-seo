"""
Vistas para la aplicación Analizador SEO con IA.
"""

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings
from .models import Analisis, Hallazgo, Imagen, Enlace
from .utils import (
    obtener_codigo_estado,
    obtener_encabezados,
    obtener_metadatos,
    obtener_imagenes, 
    obtener_enlaces,  
    # encontrar_robots_sitemap, 
    calcular_puntuacion_seo, 
    obtener_urls_sitio,
    analizar_contenido_pagina, 
    verificar_archivos_seo,
    obtener_recomendacion_ia # New import for AI recommendations
)
from .forms import AnalisisForm
from django.urls import reverse
from django.db.models import Avg
from collections import defaultdict


class InicioView(ListView):
    """
    Vista para la página de inicio que muestra el formulario de análisis
    y la lista de análisis realizados.
    """
    model = Analisis
    template_name = 'analizador/inicio.html'
    context_object_name = 'analisis'
    ordering = ['-fecha_analisis']
    paginate_by = 10


class DetalleAnalisisView(DetailView):
    """
    Vista para mostrar los detalles de un análisis SEO específico.
    """
    model = Analisis
    template_name = 'analizador/detalle_analisis.html'
    context_object_name = 'analisis'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analisis = self.get_object()
        
        # Obtener hallazgos, imágenes y enlaces
        context['hallazgos'] = analisis.hallazgos.all()
        context['imagenes'] = analisis.imagenes.all()
        context['enlaces'] = analisis.enlaces.all()

        # Obtener el contenido de robots.txt y sitemap.xml si existen
        if analisis.robots_txt:
            try:
                robots_response = requests.get(urljoin(analisis.url, '/robots.txt'), timeout=5)
                context['robots_content'] = robots_response.text if robots_response.status_code == 200 else None
            except:
                context['robots_content'] = None

        if analisis.sitemap_xml:
            try:
                sitemap_response = requests.get(urljoin(analisis.url, '/sitemap.xml'), timeout=5)
                context['sitemap_content'] = sitemap_response.text if sitemap_response.status_code == 200 else None
            except:
                context['sitemap_content'] = None

        # Obtener todas las páginas analizadas del mismo dominio
        dominio_base = urlparse(analisis.url).netloc
        context['paginas_analizadas'] = Analisis.objects.filter(
            url__contains=dominio_base,
            fecha_analisis=analisis.fecha_analisis
        ).exclude(pk=analisis.pk)

        return context


class ResumenAnalisisView(DetailView):
    """
    Vista para mostrar el resumen general de todas las URLs analizadas
    """
    model = Analisis
    template_name = 'analizador/resumen_analisis.html'
    context_object_name = 'analisis_principal'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analisis_principal = self.get_object()
        
        # Obtener todas las URLs analizadas (principal + relacionadas)
        context['urls_analizadas'] = [analisis_principal] + list(analisis_principal.urls_analizadas.all())
        
        # Estadísticas generales
        context['total_urls'] = len(context['urls_analizadas'])
        context['puntuacion_promedio'] = sum(url.puntuacion for url in context['urls_analizadas']) / context['total_urls'] if context['total_urls'] > 0 else 0

        # Inicializar conteo de hallazgos por tipo con valores por defecto
        hallazgos_totales = defaultdict(int)
        
        # Contar hallazgos
        for analisis in context['urls_analizadas']:
            for hallazgo in analisis.hallazgos.all():
                hallazgos_totales[hallazgo.tipo] += 1

        context['hallazgos_totales'] = dict(hallazgos_totales)
        context['total_hallazgos'] = sum(hallazgos_totales.values())

        # Obtener el contenido de robots.txt y sitemap.xml
        try:
            robots_url = urljoin(analisis_principal.url, '/robots.txt')
            robots_response = requests.get(robots_url, timeout=5)
            context['robots_content'] = robots_response.text if robots_response.status_code == 200 else None
        except:
            context['robots_content'] = None

        try:
            sitemap_url = urljoin(analisis_principal.url, '/sitemap.xml')
            sitemap_response = requests.get(sitemap_url, timeout=5)
            context['sitemap_content'] = sitemap_response.text if sitemap_response.status_code == 200 else None
        except:
            context['sitemap_content'] = None

        return context


# obtener_urls_sitio function has been moved to utils.py


def inicio(request):
    form = AnalisisForm()
    if request.method == 'POST':
        form = AnalisisForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            crawl_scope = form.cleaned_data['crawl_scope']
            num_pages = form.cleaned_data.get('num_pages') # Can be None
            website_technology = form.cleaned_data.get('website_technology')

            # Conjunto para almacenar todas las URLs encontradas
            urls_visitadas = set()
            urls_por_visitar = {url}

            if crawl_scope == 'single_url':
                max_urls = 1
            else: # multiple_pages
                max_urls = num_pages if num_pages else 10 # Default to 10 if not provided for some reason

            # Crear el análisis principal
            analisis_principal = None
            analisis_relacionados = []
            
            # Realizar crawling del sitio
            while urls_por_visitar and len(urls_visitadas) < max_urls:
                url_actual = urls_por_visitar.pop()
                
                if url_actual in urls_visitadas:
                    continue
                
                try:
                    # Realizar el análisis de la URL actual
                    response = requests.get(url_actual, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Inicializar puntuación para la página actual
                    puntuacion_pagina = 100 # Start with a base score for the page

                    # Analizar contenido de la página usando la nueva función de utils.py
                    contenido_info = analizar_contenido_pagina(soup, url_actual, website_technology)
                    
                    # Extraer datos del resultado de analizar_contenido_pagina
                    titulo_pagina = contenido_info['titulo'] if contenido_info['titulo'] else url_actual # Use URL if title is empty
                    descripcion_pagina = contenido_info['descripcion_meta']
                    
                    # Lista para todos los hallazgos (de contenido y de archivos SEO)
                    todos_hallazgos_info_pagina = list(contenido_info['hallazgos_info']) # Make a mutable copy

                    # Ajustar puntuación basada en hallazgos de contenido (ejemplo)
                    # This simplistic scoring adjustment should be refined or replaced by calcular_puntuacion_seo
                    for hallazgo_item in todos_hallazgos_info_pagina:
                        if hallazgo_item['tipo'] == 'error':
                            puntuacion_pagina -= 10
                        elif hallazgo_item['tipo'] == 'warning':
                            puntuacion_pagina -= 5
                        elif hallazgo_item['tipo'] == 'info': # Infos usually don't decrease score, but can
                            puntuacion_pagina -= 1
                    
                    # Crear el objeto Analisis
                    current_analisis_data = {
                        'url': url_actual,
                        'titulo': titulo_pagina,
                        'descripcion': descripcion_pagina,
                        'codigo_estado': response.status_code,
                        'robots_txt': False,  # Default, será actualizado para la URL principal
                        'sitemap_xml': False, # Default, será actualizado para la URL principal
                        # 'puntuacion' se establecerá después de considerar archivos SEO si es la URL principal
                    }

                    if url_actual == url: # Es la URL principal del análisis
                        current_analisis_data['crawl_scope'] = crawl_scope
                        current_analisis_data['num_pages_solicitadas'] = num_pages if crawl_scope == 'multiple_pages' else 1
                        current_analisis_data['tecnologia_sitio'] = website_technology
                        
                        # Verificar robots.txt y sitemap.xml para la URL principal
                        archivos_seo_info = verificar_archivos_seo(url)
                        current_analisis_data['robots_txt'] = archivos_seo_info['robots_txt_exists']
                        current_analisis_data['sitemap_xml'] = archivos_seo_info['sitemap_xml_exists']
                        todos_hallazgos_info_pagina.extend(archivos_seo_info['hallazgos_info'])

                        # Ajustar puntuación por archivos SEO (ejemplo)
                        if not archivos_seo_info['robots_txt_exists']:
                            puntuacion_pagina -= 2 # Similar to old logic
                        if not archivos_seo_info['sitemap_xml_exists']:
                            puntuacion_pagina -= 2 # Similar to old logic
                    
                    current_analisis_data['puntuacion'] = max(0, min(100, puntuacion_pagina))
                    analisis_actual = Analisis.objects.create(**current_analisis_data)

                    # Guardar el análisis principal o agregarlo a la lista de relacionados
                    if url_actual == url:
                        analisis_principal = analisis_actual
                    else:
                        analisis_relacionados.append(analisis_actual)

                    # Guardar Hallazgos (con recomendaciones IA)
                    for hallazgo_data in todos_hallazgos_info_pagina:
                        # Generate AI recommendation for each original finding
                        recomendacion_ai = obtener_recomendacion_ia(
                            hallazgo_descripcion=hallazgo_data['descripcion'],
                            url_pagina=url_actual,
                            tecnologia_sitio=website_technology, # from form.cleaned_data
                            tipo_hallazgo=hallazgo_data['tipo']
                        )
                        
                        # Create a new Hallazgo for the AI recommendation
                        Hallazgo.objects.create(
                            analisis=analisis_actual,
                            tipo='recomendacion', # All AI-generated advice is a 'recomendacion'
                            descripcion=recomendacion_ai 
                        )
                        
                        # Optionally, you might still want to save the original finding if it's distinct
                        # from the recommendation or if recommendations are supplementary.
                        # For this subtask, we are replacing/focusing on the AI recommendation.
                        # If original findings are still needed, they should be created here as well:
                        # Hallazgo.objects.create(
                        #     analisis=analisis_actual,
                        #     tipo=hallazgo_data['tipo'], # Original type
                        #     descripcion=hallazgo_data['descripcion'] # Original description
                        # )


                    # Guardar Imágenes
                    for img_data in contenido_info['imagenes_info']:
                        Imagen.objects.create(
                            analisis=analisis_actual,
                            url=img_data['url'],
                            alt=img_data['alt']
                        )
                    
                    # Guardar Enlaces
                    for enlace_data in contenido_info['enlaces_info']:
                        Enlace.objects.create(
                            analisis=analisis_actual,
                            url=enlace_data['url'],
                            texto=enlace_data['texto'],
                            tipo=enlace_data['tipo']
                        )
                    
                    # Obtener nuevas URLs para crawlear (si aplica)
                    if crawl_scope == 'multiple_pages':
                        # urls_visitadas se usa para no agregar URLs ya procesadas o en cola
                        # max_urls es el límite global
                        if len(urls_visitadas) < max_urls:
                            nuevas_urls = obtener_urls_sitio(url_actual, soup, urls_visitadas.union(urls_por_visitar))
                            for nueva_url in nuevas_urls:
                                if len(urls_visitadas) + len(urls_por_visitar) < max_urls:
                                     urls_por_visitar.add(nueva_url)
                                else:
                                    break # Stop adding if we've hit the limit

                    # Marcar URL como visitada
                    urls_visitadas.add(url_actual)

                except requests.RequestException as e:
                    messages.warning(request, f"Error al acceder a {url_actual}: {str(e)}. Saltando esta URL.")
                    urls_visitadas.add(url_actual) # Marcar como visitada para no reintentar
                    continue
                except Exception as e: # Captura general para otros errores inesperados durante el análisis de una página
                    messages.error(request, f"Error inesperado analizando {url_actual}: {str(e)}. Saltando esta URL.")
                    urls_visitadas.add(url_actual) # Marcar como visitada para no reintentar
                    continue

            if analisis_principal:
                # Actualizar la relación entre análisis (si hay análisis relacionados)
                for analisis in analisis_relacionados:
                    analisis.analisis_principal = analisis_principal
                    analisis.save()

                messages.success(request, f'Análisis completado. Se procesaron {len(urls_visitadas)} página(s).')
                return redirect('analizador:resumen_analisis', pk=analisis_principal.pk)
            elif not urls_visitadas and crawl_scope == 'single_url': # Failed to analyze even the single main URL
                 messages.error(request, f'No se pudo analizar la URL proporcionada: {url}. Verifique la URL e intente de nuevo.')
            elif not urls_visitadas and crawl_scope == 'multiple_pages':
                 messages.error(request, f'No se pudo analizar la URL inicial: {url}. No se pudieron rastrear más páginas.')
            else: # Should ideally be caught by specific errors, but as a fallback
                 messages.info(request, f'Análisis finalizado. Se procesaron {len(urls_visitadas)} páginas, pero la URL principal no pudo ser completamente analizada o no se encontraron páginas adicionales.')


        else: # Form is not valid
            # Django renders form errors automatically via {% bootstrap_form form %}
            pass

    analisis_recientes = Analisis.objects.filter(
        analisis_principal__isnull=True
    ).order_by('-fecha_analisis')[:10]
    return render(request, 'analizador/inicio.html', {'form': form, 'analisis_recientes': analisis_recientes})


def detalle_analisis(request, pk):
    """Vista para mostrar los detalles de un análisis."""
    analisis = get_object_or_404(Analisis, pk=pk)
    return render(request, 'analizador/detalle_analisis.html', {'analisis': analisis}) 