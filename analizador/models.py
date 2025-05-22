"""
Modelos para la aplicación Analizador SEO con IA.
"""

from django.db import models
from django.utils import timezone


class Analisis(models.Model):
    """
    Modelo para almacenar los resultados del análisis SEO.
    """
    url = models.URLField(max_length=500, verbose_name='URL')
    fecha_analisis = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Análisis')
    puntuacion = models.IntegerField(verbose_name='Puntuación SEO', default=0)
    codigo_estado = models.IntegerField(verbose_name='Código de Estado')
    titulo = models.CharField(max_length=200, blank=True, verbose_name='Título')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    robots_txt = models.BooleanField(default=False, verbose_name='Contenido robots.txt')
    sitemap_xml = models.BooleanField(default=False, verbose_name='Contenido sitemap.xml')

    # New fields for crawl scope and technology
    crawl_scope = models.CharField(
        max_length=20,
        choices=[('single_url', 'Single URL'), ('multiple_pages', 'Multiple Pages')],
        default='single_url',
        verbose_name='Crawl Scope'
    )
    num_pages_solicitadas = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Number of Pages Requested'
    )
    tecnologia_sitio = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Website Technology'
    )

    analisis_principal = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='urls_analizadas'
    )
    
    class Meta:
        verbose_name = 'Análisis SEO'
        verbose_name_plural = 'Análisis SEO'
        ordering = ['-fecha_analisis']
    
    def __str__(self):
        return f"Análisis de {self.url} - {self.fecha_analisis}"


class Hallazgo(models.Model):
    """
    Modelo para almacenar los hallazgos del análisis SEO.
    """
    TIPOS = [
        ('error', 'Error'),
        ('warning', 'Advertencia'),
        ('info', 'Información'),
        ('recomendacion', 'Recomendación'),
    ]
    
    analisis = models.ForeignKey(Analisis, on_delete=models.CASCADE, related_name='hallazgos')
    tipo = models.CharField(max_length=20, choices=TIPOS, verbose_name='Tipo')
    descripcion = models.TextField(verbose_name='Descripción')
    fecha = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Creación')
    
    class Meta:
        verbose_name = 'Hallazgo'
        verbose_name_plural = 'Hallazgos'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.get_tipo_display()}: {self.descripcion[:50]}..."


class Imagen(models.Model):
    """
    Modelo para almacenar información sobre las imágenes encontradas.
    """
    analisis = models.ForeignKey(Analisis, on_delete=models.CASCADE, related_name='imagenes')
    url = models.URLField(max_length=500, verbose_name='URL de la Imagen')
    alt = models.CharField(max_length=200, blank=True, verbose_name='Texto Alternativo')
    fecha = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Creación')
    
    class Meta:
        verbose_name = 'Imagen'
        verbose_name_plural = 'Imágenes'
        ordering = ['url']
    
    def __str__(self):
        return f"Imagen: {self.url}"


class Enlace(models.Model):
    """
    Modelo para almacenar información sobre los enlaces encontrados.
    """
    analisis = models.ForeignKey(Analisis, on_delete=models.CASCADE, related_name='enlaces')
    url = models.URLField(max_length=500, verbose_name='URL del Enlace')
    texto = models.CharField(max_length=200, blank=True, verbose_name='Texto del Enlace')
    tipo = models.CharField(max_length=20, choices=[
        ('interno', 'Interno'),
        ('externo', 'Externo')
    ], default='externo')
    fecha = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Creación')
    
    class Meta:
        verbose_name = 'Enlace'
        verbose_name_plural = 'Enlaces'
        ordering = ['url']
    
    def __str__(self):
        return f"{self.tipo}: {self.url}" 