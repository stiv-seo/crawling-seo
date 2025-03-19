from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Analisis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(max_length=500, verbose_name='URL')),
                ('fecha_analisis', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de Análisis')),
                ('titulo', models.CharField(blank=True, max_length=200, verbose_name='Título')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('codigo_estado', models.IntegerField(verbose_name='Código de Estado')),
                ('puntuacion', models.IntegerField(default=0, verbose_name='Puntuación SEO')),
                ('robots_txt', models.TextField(blank=True, verbose_name='robots.txt')),
                ('sitemap_xml', models.TextField(blank=True, verbose_name='sitemap.xml')),
            ],
            options={
                'verbose_name': 'Análisis',
                'verbose_name_plural': 'Análisis',
                'ordering': ['-fecha_analisis'],
            },
        ),
        migrations.CreateModel(
            name='Enlace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(max_length=500, verbose_name='URL del Enlace')),
                ('texto', models.CharField(blank=True, max_length=200, verbose_name='Texto del Enlace')),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de Creación')),
                ('analisis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enlaces', to='analizador.analisis', verbose_name='Análisis')),
            ],
            options={
                'verbose_name': 'Enlace',
                'verbose_name_plural': 'Enlaces',
                'ordering': ['-fecha'],
            },
        ),
        migrations.CreateModel(
            name='Imagen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(max_length=500, verbose_name='URL de la Imagen')),
                ('texto_alternativo', models.CharField(blank=True, max_length=200, verbose_name='Texto Alternativo')),
                ('formato', models.CharField(max_length=10, verbose_name='Formato')),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de Creación')),
                ('analisis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imagenes', to='analizador.analisis', verbose_name='Análisis')),
            ],
            options={
                'verbose_name': 'Imagen',
                'verbose_name_plural': 'Imágenes',
                'ordering': ['-fecha'],
            },
        ),
        migrations.CreateModel(
            name='Hallazgo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('error', 'Error'), ('warning', 'Advertencia'), ('info', 'Información')], max_length=10, verbose_name='Tipo')),
                ('mensaje', models.TextField(verbose_name='Mensaje')),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de Creación')),
                ('analisis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hallazgos', to='analizador.analisis', verbose_name='Análisis')),
            ],
            options={
                'verbose_name': 'Hallazgo',
                'verbose_name_plural': 'Hallazgos',
                'ordering': ['-fecha'],
            },
        ),
    ] 