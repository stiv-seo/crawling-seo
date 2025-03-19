"""
Configuración del panel de administración para la aplicación Analizador SEO con IA.
"""

from django.contrib import admin
from .models import Analisis, Hallazgo, Imagen, Enlace

@admin.register(Analisis)
class AnalisisAdmin(admin.ModelAdmin):
    list_display = ('url', 'fecha_analisis', 'puntuacion', 'codigo_estado')
    list_filter = ('fecha_analisis', 'codigo_estado')
    search_fields = ('url', 'titulo', 'descripcion')
    readonly_fields = ('fecha_analisis',)
    ordering = ('-fecha_analisis',)

@admin.register(Hallazgo)
class HallazgoAdmin(admin.ModelAdmin):
    list_display = ('analisis', 'tipo', 'descripcion', 'fecha')
    list_filter = ('tipo', 'fecha')
    search_fields = ('descripcion', 'analisis__url')
    readonly_fields = ('fecha',)
    ordering = ('-fecha',)

@admin.register(Imagen)
class ImagenAdmin(admin.ModelAdmin):
    list_display = ('analisis', 'url', 'alt', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('url', 'alt', 'analisis__url')
    readonly_fields = ('fecha',)
    ordering = ('-fecha',)

@admin.register(Enlace)
class EnlaceAdmin(admin.ModelAdmin):
    list_display = ('analisis', 'url', 'texto', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('url', 'texto', 'analisis__url')
    readonly_fields = ('fecha',)
    ordering = ('-fecha',) 