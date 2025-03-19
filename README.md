# Analizador SEO con IA

Herramienta de análisis SEO que realiza un crawling completo de sitios web y proporciona recomendaciones detalladas para mejorar el posicionamiento.

## Características

- Análisis completo de múltiples páginas dentro del mismo dominio
- Evaluación de más de 20 factores SEO importantes
- Puntuación detallada para cada página analizada
- Detección y análisis de robots.txt y sitemap.xml
- Análisis de enlaces internos y externos
- Verificación de imágenes y textos alternativos
- Recomendaciones personalizadas basadas en hallazgos

## Requisitos

- Python 3.8+
- Django 4.2+
- BeautifulSoup4
- Requests

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

1. Acceder a la aplicación en `http://localhost:8000`
2. Ingresar la URL del sitio a analizar
3. Esperar mientras se realiza el análisis completo
4. Revisar el resumen y las recomendaciones detalladas

## Estructura del Proyecto

```
analizador/
├── admin.py         # Configuración del panel de administración
├── models.py        # Modelos de datos
├── views.py         # Lógica de las vistas
├── urls.py          # Configuración de URLs
├── utils.py         # Funciones auxiliares
└── templates/       # Plantillas HTML
    └── analizador/
        ├── inicio.html
        ├── detalle_analisis.html
        └── resumen_analisis.html
```

## Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Tu Nombre - [@tutwitter](https://twitter.com/tutwitter) - email@ejemplo.com

Link del Proyecto: [https://github.com/tu-usuario/analizador-seo-ia](https://github.com/tu-usuario/analizador-seo-ia) 