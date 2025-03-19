"""
URLs para la aplicación Analizador SEO con IA.
"""

from django.urls import path
from . import views

app_name = 'analizador'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('analisis/<int:pk>/', views.DetalleAnalisisView.as_view(), name='detalle_analisis'),
    path('resumen/<int:pk>/', views.ResumenAnalisisView.as_view(), name='resumen_analisis'),
] 