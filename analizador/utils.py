"""
Funciones de utilidad para la aplicación Analizador SEO con IA.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re


def obtener_codigo_estado(url):
    """
    Obtiene el código de estado HTTP de una URL.
    """
    try:
        response = requests.get(url, timeout=5)
        return response.status_code
    except requests.RequestException:
        return None


def obtener_encabezados(soup):
    """
    Obtiene las etiquetas de encabezado (h1, h2, h3) de una URL.
    """
    encabezados = {"h1": [], "h2": [], "h3": []}
    
    for tag in encabezados.keys():
        encabezados[tag] = [h.get_text(strip=True) for h in soup.find_all(tag)]
    
    return encabezados


def obtener_metadatos(soup, tipo):
    """
    Obtiene los metadatos específicos de una URL.
    """
    if tipo == 'title':
        return soup.title.string if soup.title else ""
    elif tipo == 'description':
        meta = soup.find("meta", attrs={"name": "description"})
        return meta.get("content", "") if meta else ""
    return ""


def obtener_imagenes(soup, url):
    """
    Obtiene información sobre las imágenes de una URL.
    """
    imagenes = []
    
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src and not src.startswith("http"):
            src = urljoin(url, src)
        alt = img.get("alt", "")
        imagenes.append({"src": src, "alt": alt})
    
    return imagenes


def obtener_enlaces(soup, url):
    """
    Obtiene los enlaces de una URL.
    """
    enlaces = []
    
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if href and not href.startswith("#") and not href.startswith("javascript:"):
            # Convertir enlaces relativos a absolutos
            if not href.startswith("http"):
                href = urljoin(url, href)
            text = a.get_text(strip=True)
            enlaces.append({"url": href, "text": text})
    
    return enlaces


def encontrar_robots_sitemap(url, tipo):
    """
    Encuentra y obtiene el contenido de robots.txt o sitemap.xml.
    """
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    target_url = urljoin(base_url, f"/{tipo}")
    
    try:
        response = requests.get(target_url, timeout=5)
        return response.text if response.status_code == 200 else ""
    except:
        return ""


def calcular_puntuacion_seo(analisis):
    """
    Calcula la puntuación SEO basada en los hallazgos del análisis.
    """
    puntuacion = 100
    
    # Penalizaciones
    if not analisis.titulo:
        puntuacion -= 10
    elif len(analisis.titulo) < 30 or len(analisis.titulo) > 60:
        puntuacion -= 5
    
    if not analisis.descripcion:
        puntuacion -= 10
    elif len(analisis.descripcion) < 120 or len(analisis.descripcion) > 160:
        puntuacion -= 5
    
    if not analisis.robots_txt:
        puntuacion -= 5
    
    if not analisis.sitemap_xml:
        puntuacion -= 5
    
    # Penalización por imágenes sin alt
    imagenes_sin_alt = analisis.imagenes.filter(alt='').count()
    puntuacion -= min(10, imagenes_sin_alt)
    
    return max(0, min(100, puntuacion)) 