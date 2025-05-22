"""
Funciones de utilidad para la aplicación Analizador SEO con IA.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import openai
import os # For API Key


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


def analizar_contenido_pagina(soup, url_actual, website_technology=None):
    """
    Analiza el contenido SEO de una página (título, meta descripción, H1, imágenes, enlaces).
    Retorna un diccionario con la información extraída y hallazgos.
    """
    # Extraer título
    titulo = soup.title.string.strip() if soup.title and soup.title.string else ''
    
    # Extraer meta descripción
    meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
    descripcion_meta = meta_desc_tag.get('content', '').strip() if meta_desc_tag else ''
    
    # Extraer H1 tags
    h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]

    hallazgos_info = []
    imagenes_info = []
    enlaces_info = []

    # --- Análisis y Hallazgos ---
    # Analizar título
    if not titulo:
        # El título se establecerá a la URL en la vista si está vacío después de esta función.
        hallazgos_info.append({
            'tipo': 'error',
            'descripcion': 'La página no tiene título. El título es crucial para el SEO.'
            # 'puntuacion_delta': -10 # Example if returning score changes
        })
    elif len(titulo) < 10:
        hallazgos_info.append({
            'tipo': 'warning',
            'descripcion': 'El título es demasiado corto. Se recomienda entre 50-60 caracteres.'
            # 'puntuacion_delta': -5
        })
    elif len(titulo) > 60:
        hallazgos_info.append({
            'tipo': 'info',
            'descripcion': 'El título es demasiado largo. Se recomienda acortarlo a 50-60 caracteres.'
            # 'puntuacion_delta': -3
        })

    # Analizar meta descripción
    if not descripcion_meta:
        hallazgos_info.append({
            'tipo': 'error',
            'descripcion': 'No se encontró meta descripción. Es importante para el SEO.'
            # 'puntuacion_delta': -10
        })
    elif len(descripcion_meta) < 50:
        hallazgos_info.append({
            'tipo': 'warning',
            'descripcion': 'La meta descripción es demasiado corta. Se recomienda entre 150-160 caracteres.'
            # 'puntuacion_delta': -5
        })
    elif len(descripcion_meta) > 160:
        hallazgos_info.append({
            'tipo': 'info',
            'descripcion': 'La meta descripción es demasiado larga. Se recomienda acortarla a 150-160 caracteres.'
            # 'puntuacion_delta': -3
        })

    # Analizar encabezados H1
    if not h1_tags:
        hallazgos_info.append({
            'tipo': 'error',
            'descripcion': 'No se encontró encabezado H1. Cada página debe tener un H1.'
            # 'puntuacion_delta': -10
        })
    elif len(h1_tags) > 1:
        hallazgos_info.append({
            'tipo': 'warning',
            'descripcion': 'Múltiples encabezados H1 encontrados. Se recomienda usar solo uno.'
            # 'puntuacion_delta': -5
        })

    # Analizar imágenes (reutilizando la función obtener_imagenes)
    # La función obtener_imagenes ya devuelve {'src': ..., 'alt': ...}
    temp_imagenes = obtener_imagenes(soup, url_actual) 
    for img_data in temp_imagenes:
        imagenes_info.append({'url': img_data['src'], 'alt': img_data['alt']})
        if not img_data['alt']:
            hallazgos_info.append({
                'tipo': 'warning',
                'descripcion': f"Imagen sin texto alternativo: {img_data['src']}"
                # 'puntuacion_delta': -2 # Per image, might be too much, handle in view
            })

    # Analizar enlaces (reutilizando la función obtener_enlaces)
    dominio_base_actual = urlparse(url_actual).netloc
    temp_enlaces = obtener_enlaces(soup, url_actual) # devuelve {'url': ..., 'text': ...}
    enlaces_internos_count = 0
    enlaces_externos_count = 0

    for enlace_data in temp_enlaces:
        tipo_enlace = 'interno' if urlparse(enlace_data['url']).netloc == dominio_base_actual else 'externo'
        if tipo_enlace == 'interno':
            enlaces_internos_count += 1
        else:
            enlaces_externos_count += 1
        enlaces_info.append({
            'url': enlace_data['url'],
            'texto': enlace_data['text'],
            'tipo': tipo_enlace
        })

    if enlaces_internos_count < 3:
        hallazgos_info.append({
            'tipo': 'warning',
            'descripcion': 'Pocos enlaces internos. Se recomienda más enlaces para mejorar la navegación.'
            # 'puntuacion_delta': -5
        })
    if enlaces_externos_count < 1: # Original view logic was < 2, but a single external link is fine.
        hallazgos_info.append({
            'tipo': 'info', # This was 'info' in the view
            'descripcion': 'Pocos enlaces externos. Los enlaces a sitios autoritativos pueden mejorar el SEO.'
            # 'puntuacion_delta': -3
        })
        
    return {
        'titulo': titulo, # Devolver el título extraído (puede ser vacío)
        'descripcion_meta': descripcion_meta,
        'hallazgos_info': hallazgos_info,
        'imagenes_info': imagenes_info,
        'enlaces_info': enlaces_info,
        'h1_tags': h1_tags # Devolver para referencia si es necesario
    }


def verificar_archivos_seo(url_base):
    """
    Verifica la presencia de robots.txt y sitemap.xml en el sitio base.
    Retorna un diccionario con los resultados y hallazgos.
    """
    resultados = {
        'robots_txt_exists': False,
        'sitemap_xml_exists': False,
        'hallazgos_info': []
        # 'puntuacion_delta': 0 # Example
    }
    parsed_url = urlparse(url_base)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    # Verificar robots.txt
    try:
        robots_url_check = urljoin(base_url, 'robots.txt')
        robots_response = requests.get(robots_url_check, timeout=5)
        if robots_response.status_code == 200 and robots_response.text.strip(): # Check content not empty
            resultados['robots_txt_exists'] = True
        else:
            resultados['hallazgos_info'].append({
                'tipo': 'info', 
                'descripcion': 'No se encontró archivo robots.txt o está vacío.'
                # 'puntuacion_delta': -2 # Example, was -2 in view
            })
    except requests.RequestException:
        resultados['hallazgos_info'].append({
            'tipo': 'warning', # More severe than just not finding
            'descripcion': f'Error al intentar acceder a {robots_url_check}.'
        })

    # Verificar sitemap.xml
    try:
        sitemap_url_check = urljoin(base_url, 'sitemap.xml')
        sitemap_response = requests.get(sitemap_url_check, timeout=5)
        if sitemap_response.status_code == 200 and sitemap_response.text.strip(): # Check content not empty
            resultados['sitemap_xml_exists'] = True
        else:
            resultados['hallazgos_info'].append({
                'tipo': 'info',
                'descripcion': 'No se encontró archivo sitemap.xml o está vacío.'
                # 'puntuacion_delta': -2 # Example, was -2 in view
            })
    except requests.RequestException:
        resultados['hallazgos_info'].append({
            'tipo': 'warning',
            'descripcion': f'Error al intentar acceder a {sitemap_url_check}.'
        })
        
    return resultados


def obtener_recomendacion_ia(hallazgo_descripcion, url_pagina, tecnologia_sitio, tipo_hallazgo):
    """
    Generates an AI-powered SEO recommendation.
    For now, uses placeholder logic.
    """
    # TODO: Replace placeholder below with actual LLM API call and response handling.
    # Consider adding error handling for API calls.
    # openai.api_key = os.getenv("OPENAI_API_KEY")
    # prompt = f"As an expert SEO consultant, provide a specific, actionable recommendation to address the following SEO issue found on the page {url_pagina}. The website is built with {tecnologia_sitio}.\n\nSEO Issue ({tipo_hallazgo}): {hallazgo_descripcion}\n\nRecommendation:"
    # try:
    #     response = openai.Completion.create( # Or use openai.ChatCompletion.create for newer models
    #         engine="text-davinci-003", # Or a chat model like "gpt-3.5-turbo"
    #         prompt=prompt,
    #         max_tokens=150,
    #         temperature=0.7,
    #     )
    #     recommendation = response.choices[0].text.strip()
    #     return f"AI Recommendation: {recommendation}"
    # except Exception as e:
    #     return f"AI Recommendation (Error: Could not fetch): To fix '{hallazgo_descripcion}' on {url_pagina}, review SEO best practices for {tecnologia_sitio}."

    if tecnologia_sitio == 'wordpress':
        return f"AI Recommendation for WordPress: To fix '{hallazgo_descripcion}' on {url_pagina}, you should consider using a plugin like Yoast SEO or Rank Math to edit the element (e.g., title, meta description, image alt text). After editing, ensure the new content meets SEO best practices for length, keywords, and clarity. For H1 tags, you might need to edit your theme's template files or use a page builder if one is active."
    elif tecnologia_sitio == 'react' or tecnologia_sitio == 'angular' or tecnologia_sitio == 'vuejs':
        return f"AI Recommendation for {tecnologia_sitio.capitalize()} SPA: To fix '{hallazgo_descripcion}' on {url_pagina}, you'll likely need to modify the relevant component's code. For issues like titles or meta descriptions, use libraries such as React Helmet (for React), Angular Meta, or vue-meta. For content issues like H1 tags or image alt texts, directly edit the JSX/template. Ensure your pre-rendering or Server-Side Rendering (SSR) setup correctly serves these changes to search engine crawlers."
    elif tecnologia_sitio == 'shopify':
        return f"AI Recommendation for Shopify: To fix '{hallazgo_descripcion}' on {url_pagina}, you can typically edit this through the Shopify admin panel. For product pages, edit the 'Search engine listing preview'. For other pages or theme elements (like H1s), you might need to edit your theme's Liquid files (e.g., `product.liquid`, `article.liquid`, or sections)."
    elif tecnologia_sitio == 'django':
        return f"AI Recommendation for Django: To fix '{hallazgo_descripcion}' on {url_pagina}, you will likely need to modify the Django template responsible for rendering this page (e.g., an `.html` file in your app's `templates` directory). For titles or meta descriptions, ensure they are passed from the view to the template context and rendered in the `<head>`. For H1s or image alts, modify the content directly in the template tags or context variables."
    else: # Generic or other technologies
        return f"AI Recommendation (Generic for {tecnologia_sitio if tecnologia_sitio else 'your website'}): To fix '{hallazgo_descripcion}' on {url_pagina}, identify where this content is generated in your {tecnologia_sitio if tecnologia_sitio else 'website'} setup (e.g., template files, CMS settings, component code) and modify it according to SEO best practices. Ensure changes improve relevance and user experience."