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
    encontrar_robots_sitemap,
    calcular_puntuacion_seo
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


def obtener_urls_sitio(url_base, soup, urls_visitadas=None, max_urls=100):
    """
    Función recursiva para obtener todas las URLs del sitio.
    """
    if urls_visitadas is None:
        urls_visitadas = set()
    
    # Obtener el dominio base
    dominio_base = urlparse(url_base).netloc
    urls_encontradas = set()

    # Encontrar todos los enlaces en la página actual
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        if href:
            # Convertir URL relativa a absoluta
            url_absoluta = urljoin(url_base, href)
            
            # Verificar que la URL pertenece al mismo dominio
            if urlparse(url_absoluta).netloc == dominio_base:
                # Limpiar la URL (eliminar fragmentos y parámetros de consulta)
                url_limpia = url_absoluta.split('#')[0].split('?')[0]
                
                # Agregar la URL si no ha sido visitada y no excede el límite
                if url_limpia not in urls_visitadas and len(urls_visitadas) < max_urls:
                    urls_encontradas.add(url_limpia)

    return urls_encontradas


def inicio(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        try:
            # Validar URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Conjunto para almacenar todas las URLs encontradas
            urls_visitadas = set()
            urls_por_visitar = {url}
            max_urls = 50  # Límite de URLs a analizar

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

                    # Inicializar puntuación
                    puntuacion = 100
                    hallazgos = []

                    # Analizar título
                    titulo = soup.title.string if soup.title else url_actual
                    if not titulo:
                        titulo = url_actual  # Usar la URL como título si no hay título
                        puntuacion -= 10
                        hallazgos.append(Hallazgo(
                            tipo='error',
                            descripcion='La página no tiene título. El título es crucial para el SEO.'
                        ))
                    elif len(titulo) < 10:
                        puntuacion -= 5
                        hallazgos.append(Hallazgo(
                            tipo='warning',
                            descripcion='El título es demasiado corto. Se recomienda entre 50-60 caracteres.'
                        ))
                    elif len(titulo) > 60:
                        puntuacion -= 3
                        hallazgos.append(Hallazgo(
                            tipo='info',
                            descripcion='El título es demasiado largo. Se recomienda acortarlo a 50-60 caracteres.'
                        ))

                    # Analizar meta descripción
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    descripcion = meta_desc.get('content', '') if meta_desc else ''
                    if not descripcion:
                        puntuacion -= 10
                        hallazgos.append(Hallazgo(
                            tipo='error',
                            descripcion='No se encontró meta descripción. Es importante para el SEO.'
                        ))
                    elif len(descripcion) < 50:
                        puntuacion -= 5
                        hallazgos.append(Hallazgo(
                            tipo='warning',
                            descripcion='La meta descripción es demasiado corta. Se recomienda entre 150-160 caracteres.'
                        ))
                    elif len(descripcion) > 160:
                        puntuacion -= 3
                        hallazgos.append(Hallazgo(
                            tipo='info',
                            descripcion='La meta descripción es demasiado larga. Se recomienda acortarla a 150-160 caracteres.'
                        ))

                    # Analizar encabezados
                    h1_tags = soup.find_all('h1')
                    if not h1_tags:
                        puntuacion -= 10
                        hallazgos.append(Hallazgo(
                            tipo='error',
                            descripcion='No se encontró encabezado H1. Cada página debe tener un H1.'
                        ))
                    elif len(h1_tags) > 1:
                        puntuacion -= 5
                        hallazgos.append(Hallazgo(
                            tipo='warning',
                            descripcion='Múltiples encabezados H1 encontrados. Se recomienda usar solo uno.'
                        ))

                    # Crear el análisis
                    analisis = Analisis.objects.create(
                        url=url_actual,
                        titulo=titulo,
                        descripcion=descripcion,
                        codigo_estado=response.status_code,
                        robots_txt=False,
                        sitemap_xml=False,
                        puntuacion=max(0, min(100, puntuacion))
                    )

                    # Guardar el análisis principal o agregarlo a la lista de relacionados
                    if url_actual == url:
                        analisis_principal = analisis
                    else:
                        analisis_relacionados.append(analisis)

                    # Guardar hallazgos
                    for hallazgo in hallazgos:
                        hallazgo.analisis = analisis
                        hallazgo.save()

                    # Analizar imágenes
                    for img in soup.find_all('img'):
                        img_url = img.get('src', '')
                        if img_url:
                            img_url = urljoin(url_actual, img_url)
                            alt_text = img.get('alt', '')
                            if not alt_text:
                                puntuacion -= 2
                                Hallazgo.objects.create(
                                    analisis=analisis,
                                    tipo='warning',
                                    descripcion=f'Imagen sin texto alternativo: {img_url}'
                                )
                            Imagen.objects.create(
                                analisis=analisis,
                                url=img_url,
                                alt=alt_text
                            )

                    # Analizar enlaces y obtener nuevas URLs
                    enlaces_internos = 0
                    enlaces_externos = 0
                    dominio_base = urlparse(url).netloc

                    # Obtener nuevas URLs para crawlear
                    nuevas_urls = obtener_urls_sitio(url_actual, soup, urls_visitadas)
                    urls_por_visitar.update(nuevas_urls)

                    for link in soup.find_all('a'):
                        href = link.get('href', '')
                        if href:
                            href_absoluto = urljoin(url_actual, href)
                            dominio_enlace = urlparse(href_absoluto).netloc
                            es_interno = dominio_enlace == dominio_base
                            
                            if es_interno:
                                enlaces_internos += 1
                            else:
                                enlaces_externos += 1

                            Enlace.objects.create(
                                analisis=analisis,
                                url=href_absoluto,
                                texto=link.get_text().strip(),
                                tipo='interno' if es_interno else 'externo'
                            )

                    if enlaces_internos < 3:
                        puntuacion -= 5
                        Hallazgo.objects.create(
                            analisis=analisis,
                            tipo='warning',
                            descripcion='Pocos enlaces internos. Se recomienda más enlaces para mejorar la navegación.'
                        )

                    if enlaces_externos < 2:
                        puntuacion -= 3
                        Hallazgo.objects.create(
                            analisis=analisis,
                            tipo='info',
                            descripcion='Pocos enlaces externos. Los enlaces a sitios autoritativos pueden mejorar el SEO.'
                        )

                    # Verificar robots.txt (solo para la URL principal)
                    if url_actual == url:
                        try:
                            robots_url = urljoin(url, '/robots.txt')
                            robots_response = requests.get(robots_url, timeout=5)
                            if robots_response.status_code == 200:
                                analisis.robots_txt = True
                                analisis.save()
                            else:
                                puntuacion -= 2
                                Hallazgo.objects.create(
                                    analisis=analisis,
                                    tipo='info',
                                    descripcion='No se encontró archivo robots.txt'
                                )
                        except:
                            pass

                        # Verificar sitemap.xml
                        try:
                            sitemap_url = urljoin(url, '/sitemap.xml')
                            sitemap_response = requests.get(sitemap_url, timeout=5)
                            if sitemap_response.status_code == 200:
                                analisis.sitemap_xml = True
                                analisis.save()
                            else:
                                puntuacion -= 2
                                Hallazgo.objects.create(
                                    analisis=analisis,
                                    tipo='info',
                                    descripcion='No se encontró archivo sitemap.xml'
                                )
                        except:
                            pass

                    # Actualizar puntuación final
                    analisis.puntuacion = max(0, min(100, puntuacion))
                    analisis.save()

                    # Marcar URL como visitada
                    urls_visitadas.add(url_actual)

                except requests.RequestException:
                    # Si hay un error al acceder a la URL, la saltamos
                    continue

            if analisis_principal:
                # Actualizar la relación entre análisis
                for analisis in analisis_relacionados:
                    analisis.analisis_principal = analisis_principal
                    analisis.save()

                messages.success(request, f'Análisis completado exitosamente. Se analizaron {len(urls_visitadas)} páginas.')
                return redirect('analizador:resumen_analisis', pk=analisis_principal.pk)
            else:
                messages.error(request, 'No se pudo analizar la URL principal.')

        except requests.RequestException as e:
            messages.error(request, f'Error al acceder a la URL: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error durante el análisis: {str(e)}')

    # Mostrar los últimos 5 análisis
    analisis_recientes = Analisis.objects.filter(
        analisis_principal__isnull=True  # Solo URLs principales
    ).order_by('-fecha_analisis')[:10]
    return render(request, 'analizador/inicio.html', {'analisis_recientes': analisis_recientes})


def detalle_analisis(request, pk):
    """Vista para mostrar los detalles de un análisis."""
    analisis = get_object_or_404(Analisis, pk=pk)
    return render(request, 'analizador/detalle_analisis.html', {'analisis': analisis}) 