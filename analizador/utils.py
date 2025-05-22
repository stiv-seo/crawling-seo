"""
Funciones de utilidad para la aplicación Analizador SEO con IA.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
# import openai # No longer needed
import os # For API Key
import google.generativeai as genai # Added for Gemini

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
    Generates an AI-powered SEO recommendation using Google Gemini.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Consider logging this error as well for server-side visibility
        # print("Error: GEMINI_API_KEY not configured.") 
        return "Error: AI recommendations are currently unavailable (API key not configured). Please consult standard SEO best practices."

    try:
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-pro') # Or 'gemini-1.0-pro'

        prompt = f"""As an expert SEO consultant, provide a specific, actionable recommendation to address the following SEO issue.
The website is built with: {tecnologia_sitio if tecnologia_sitio else 'Unknown/Generic'}
The issue was found on the page: {url_pagina}
SEO Issue (Type: {tipo_hallazgo}): {hallazgo_descripcion}

Focus on providing a practical solution that someone can implement.
If the technology is '{tecnologia_sitio}', tailor the advice accordingly. If 'generic' or unknown, provide general advice.
If providing code examples (e.g., for React, Django, WordPress PHP), keep them brief and illustrative.
Structure your recommendation clearly. For example:
1. **Understand the Issue:** Briefly explain why this is an issue.
2. **How to Fix ({tecnologia_sitio if tecnologia_sitio else 'General'}):** Provide step-by-step instructions.
3. **Tools/Plugins (if applicable for {tecnologia_sitio if tecnologia_sitio else 'General'}):** Suggest any relevant tools or plugins.
4. **Verification:** How to check if the fix is successful.

Recommendation:
"""
        # Safety settings can be adjusted if needed
        # safety_settings = [
        #     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        #     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        #     {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        #     {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        # ]
        # response = model.generate_content(prompt, safety_settings=safety_settings)
        
        response = model.generate_content(prompt)

        if response.parts:
            # Ensure all parts are concatenated if the response is chunked.
            recommendation = ''.join(part.text for part in response.parts if part.text)
            if not recommendation.strip(): # Check if recommendation is just whitespace
                 recommendation = f"AI received an empty or non-textual response for: {hallazgo_descripcion}"
        elif response.text and response.text.strip():
            recommendation = response.text
        else: # Fallback if response.text is empty or parts are empty
            recommendation = f"AI analysis complete, but no specific textual recommendation was generated for: {hallazgo_descripcion}. Please review standard SEO best practices for this type of issue ({tipo_hallazgo})."
            
        return recommendation

    except ValueError as ve: # Handles errors like blocked prompts if safety settings are strict
        # Log the specific ValueError: print(f"ValueError from Gemini: {ve}")
        return f"AI recommendation for '{hallazgo_descripcion}' could not be generated due to content restrictions or an internal API error. Please review manually."
    except genai.types.BlockedPromptException as bpe:
        # Log the exception: print(f"BlockedPromptException from Gemini: {bpe}")
        return f"AI recommendation for '{hallazgo_descripcion}' was blocked due to content safety policies. Please review the issue manually."
    except genai.types.generation_types.StopCandidateException as sce:
        # Log the exception: print(f"StopCandidateException from Gemini: {sce}")
        return f"AI recommendation generation for '{hallazgo_descripcion}' was stopped prematurely. The issue might be too complex or the response too long. Please review manually."
    except Exception as e:
        # Log the general exception: print(f"General Error calling Gemini API: {type(e).__name__} - {e}")
        return f"AI recommendation could not be generated for '{hallazgo_descripcion}'. An unexpected error occurred with the AI service."


def obtener_urls_sitio(url_base_actual, soup, urls_globales_conocidas):
    """
    Encuentra todos los enlaces únicos dentro del mismo dominio en la página actual,
    excluyendo aquellos ya conocidos globalmente.

    Args:
        url_base_actual (str): La URL de la página que se está analizando actualmente.
        soup (BeautifulSoup): El objeto BeautifulSoup de la página actual.
        urls_globales_conocidas (set): Un conjunto de URLs que ya han sido visitadas
                                      o están en la cola de URLs por visitar.
    Returns:
        set: Un conjunto de nuevas URLs encontradas en la página actual que pertenecen
             al mismo dominio y no estaban en urls_globales_conocidas.
    """
    urls_encontradas_pagina = set()
    dominio_principal = urlparse(url_base_actual).netloc

    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if not href:
            continue

        # Ignorar enlaces ancla y JavaScript
        if href.startswith('#') or href.startswith('javascript:'):
            continue

        # Convertir URL relativa a absoluta
        url_absoluta = urljoin(url_base_actual, href)
        
        # Parsear la URL absoluta para limpiarla y verificar el dominio
        parsed_absoluta = urlparse(url_absoluta)
        
        # Verificar que la URL pertenece al mismo dominio principal
        if parsed_absoluta.netloc == dominio_principal:
            # Normalizar URL (eliminar fragmento y parámetros de consulta opcionalmente)
            # Para este caso, solo eliminamos el fragmento para evitar duplicados por anclas.
            url_limpia = parsed_absoluta._replace(fragment="").geturl()

            if url_limpia not in urls_globales_conocidas:
                urls_encontradas_pagina.add(url_limpia)
    
    return urls_encontradas_pagina