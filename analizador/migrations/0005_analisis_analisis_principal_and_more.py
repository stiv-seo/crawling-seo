# Generated by Django 4.2.7 on 2025-03-19 18:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analizador', '0004_enlace_tipo_alter_hallazgo_descripcion'),
    ]

    operations = [
        migrations.AddField(
            model_name='analisis',
            name='analisis_principal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='urls_analizadas', to='analizador.analisis'),
        ),
        migrations.AlterField(
            model_name='analisis',
            name='fecha_analisis',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Análisis'),
        ),
        migrations.AlterField(
            model_name='analisis',
            name='robots_txt',
            field=models.BooleanField(default=False, verbose_name='Contenido robots.txt'),
        ),
        migrations.AlterField(
            model_name='analisis',
            name='sitemap_xml',
            field=models.BooleanField(default=False, verbose_name='Contenido sitemap.xml'),
        ),
    ]
