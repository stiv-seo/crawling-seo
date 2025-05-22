# Analizador SEO con IA

Herramienta de análisis SEO que realiza un crawling completo de sitios web y proporciona recomendaciones detalladas para mejorar el posicionamiento.

## Características

- **Análisis Flexible:**
    - Analiza una **URL única** para un chequeo rápido.
    - Realiza un **análisis multipágina** especificando el número máximo de URLs a rastrear dentro del mismo dominio.
- Evaluación de más de 20 factores SEO importantes.
- Puntuación detallada para cada página analizada.
- Detección y análisis de `robots.txt` y `sitemap.xml`.
- Análisis de enlaces internos y externos.
- Verificación de imágenes y textos alternativos.
- **Recomendaciones Potenciadas por Google Gemini:**
    - Recibe sugerencias inteligentes y personalizadas para mejorar tu SEO, generadas por la **API de Google Gemini (modelo gemini-pro)**.
    - Las recomendaciones se adaptan a la **tecnología de tu sitio web** (ej. WordPress, Shopify, React, Django, etc.) para ofrecer consejos más precisos y prácticos.

## Requisitos

- Python 3.8+
- Django 4.2+
- BeautifulSoup4
- Requests
- google-generativeai (para la funcionalidad de recomendaciones con Google Gemini)

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd analizador-seo
```

2. Crear y activar un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. **Configurar la API Key de Gemini (para Recomendaciones IA):**

   ### Configuración de la API Key de Gemini

   Para habilitar las recomendaciones SEO potenciadas por IA, necesitas configurar tu API key de Google Gemini:

   1.  Obtén una API key desde [Google AI Studio](https://makersuite.google.com/ai-studio) (anteriormente MakerSuite) o tu proyecto en Google Cloud.
   2.  Establece esta clave como una variable de entorno llamada `GEMINI_API_KEY`. Puedes hacerlo de las siguientes maneras:
       *   **Usando un archivo `.env` (recomendado):**
           Crea un archivo llamado `.env` en la raíz del proyecto (asegúrate de que `.env` esté incluido en tu archivo `.gitignore` para no subirlo al repositorio) y añade la siguiente línea:
           ```
           GEMINI_API_KEY='TU_API_KEY_REAL_AQUI'
           ```
           La aplicación utiliza `python-dotenv` (incluido en `requirements.txt`) para cargar automáticamente las variables de este archivo.
       *   **Directamente en tu entorno de shell:**
           -   Para Linux/macOS:
               ```bash
               export GEMINI_API_KEY='TU_API_KEY_REAL_AQUI'
               ```
           -   Para Windows (Command Prompt):
               ```bash
               set GEMINI_API_KEY='TU_API_KEY_REAL_AQUI'
               ```
           -   Para Windows (PowerShell):
               ```bash
               $Env:GEMINI_API_KEY='TU_API_KEY_REAL_AQUI'
               ```
   Si la API key no está configurada, la funcionalidad de recomendaciones IA retornará un mensaje indicando que no está disponible.

5. Realizar migraciones:
```bash
python manage.py migrate
```

6. Crear superusuario (opcional):
```bash
python manage.py createsuperuser
```

7. Iniciar el servidor:
```bash
python manage.py runserver
```

## Uso

1. Acceder a la aplicación en `http://localhost:8000`.
2. Ingresar la URL del sitio a analizar.
3. Seleccionar el **Alcance del Análisis**:
    - "Analyse only the provided URL" para una única página.
    - "Analyse multiple pages" y especificar el "Número de Páginas a Analizar" para un rastreo más amplio.
4. (Opcional) Seleccionar la **Tecnología del Sitio Web** para obtener recomendaciones más ajustadas.
5. Hacer clic en "Analizar".
6. Esperar mientras se realiza el análisis.
7. Revisar el resumen general y los detalles de cada URL analizada, incluyendo los hallazgos y las recomendaciones de la IA.

## Estructura del Proyecto

```
analizador/
├── admin.py         # Configuración del panel de administración
├── models.py        # Modelos de datos
├── views.py         # Lógica de las vistas
├── urls.py          # Configuración de URLs
├── utils.py         # Funciones auxiliares (lógica de análisis, IA, etc.)
└── templates/       # Plantillas HTML
    └── analizador/
        ├── inicio.html
        ├── detalle_analisis.html
        └── resumen_analisis.html
```
La lógica principal del análisis, incluyendo la interacción con la API de Google Gemini y la extracción de datos SEO, se ha centralizado en `utils.py` para una mejor organización.

## Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia SEO de Pragma
