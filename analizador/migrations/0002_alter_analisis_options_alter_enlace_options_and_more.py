# Generated by Django 4.2.7 on 2025-03-19 16:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analizador', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='analisis',
            options={'ordering': ['-fecha_analisis'], 'verbose_name': 'Análisis SEO', 'verbose_name_plural': 'Análisis SEO'},
        ),
        migrations.AlterModelOptions(
            name='enlace',
            options={'ordering': ['url'], 'verbose_name': 'Enlace', 'verbose_name_plural': 'Enlaces'},
        ),
        migrations.AlterModelOptions(
            name='imagen',
            options={'ordering': ['url'], 'verbose_name': 'Imagen', 'verbose_name_plural': 'Imágenes'},
        ),
        migrations.AlterField(
            model_name='analisis',
            name='robots_txt',
            field=models.TextField(blank=True, verbose_name='Contenido robots.txt'),
        ),
        migrations.AlterField(
            model_name='analisis',
            name='sitemap_xml',
            field=models.TextField(blank=True, verbose_name='Contenido sitemap.xml'),
        ),
        migrations.AlterField(
            model_name='enlace',
            name='analisis',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enlaces', to='analizador.analisis'),
        ),
        migrations.AlterField(
            model_name='hallazgo',
            name='analisis',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hallazgos', to='analizador.analisis'),
        ),
        migrations.AlterField(
            model_name='imagen',
            name='analisis',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imagenes', to='analizador.analisis'),
        ),
    ]
