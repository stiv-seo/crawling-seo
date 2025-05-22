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
- **Recomendaciones Potenciadas por IA:**
    - Recibe sugerencias inteligentes y personalizadas para mejorar tu SEO.
    - Las recomendaciones se adaptan a la **tecnología de tu sitio web** (ej. WordPress, Shopify, React, Django, etc.) para ofrecer consejos más precisos.
    (*Nota: La integración completa con el modelo de lenguaje IA está en desarrollo; actualmente, se proporcionan recomendaciones basadas en plantillas avanzadas.*)

## Requisitos

- Python 3.8+
- Django 4.2+
- BeautifulSoup4
- Requests
- OpenAI (para la funcionalidad de recomendaciones IA)

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

4. Realizar migraciones:
```bash
python manage.py migrate
```

5. Crear superusuario (opcional):
```bash
python manage.py createsuperuser
```

6. Iniciar el servidor:
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
La lógica principal del análisis, incluyendo la interacción con la IA (placeholder actual) y la extracción de datos SEO, se ha centralizado en `utils.py` para una mejor organización.

## Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia SEO de Pragma
