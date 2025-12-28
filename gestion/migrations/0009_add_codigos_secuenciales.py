from django.db import migrations, models


def generar_codigos_existentes(apps, schema_editor):
    """Genera códigos únicos para registros existentes"""
    Prestamo = apps.get_model('gestion', 'Prestamo')
    Multa = apps.get_model('gestion', 'Multa')
    
    # Generar códigos para préstamos existentes
    for idx, prestamo in enumerate(Prestamo.objects.all().order_by('id'), start=1):
        prestamo.codigo = f"BLB-{idx:03d}"
        prestamo.save()
    
    # Generar códigos para multas existentes
    for idx, multa in enumerate(Multa.objects.all().order_by('id'), start=1):
        multa.codigo = f"MLT-{idx:03d}"
        multa.save()


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0008_prestamo_estado_libro'),  # ← CORRECTO según tu showmigrations
    ]

    operations = [
        # Paso 1: Agregar campos como nullable primero
        migrations.AddField(
            model_name='prestamo',
            name='codigo',
            field=models.CharField(max_length=20, null=True, blank=True, editable=False),
        ),
        migrations.AddField(
            model_name='multa',
            name='codigo',
            field=models.CharField(max_length=20, null=True, blank=True, editable=False),
        ),
        
        # Paso 2: Generar códigos para registros existentes
        migrations.RunPython(generar_codigos_existentes, migrations.RunPython.noop),
        
        # Paso 3: Hacer campos unique y NOT NULL
        migrations.AlterField(
            model_name='prestamo',
            name='codigo',
            field=models.CharField(max_length=20, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name='multa',
            name='codigo',
            field=models.CharField(max_length=20, unique=True, editable=False),
        ),
    ]
