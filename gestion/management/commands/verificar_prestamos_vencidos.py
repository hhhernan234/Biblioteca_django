from django.core.management.base import BaseCommand
from django.utils import timezone
from gestion.models import Prestamo, Multa


class Command(BaseCommand):
    help = 'Verifica préstamos vencidos y crea multas automáticamente'

    def handle(self, *args, **kwargs):
        #Ejecuta la verificación de préstamos vencidos
        fecha_actual = timezone.now().date()
        
        # Buscar préstamos en estado Prestado que ya pasaron la fecha máxima
        prestamos_vencidos = Prestamo.objects.filter(
            estado='p',
            fecha_max__lt=fecha_actual
        )
        
        multas_creadas = 0
        multas_actualizadas = 0
        
        for prestamo in prestamos_vencidos:
            # Calcular días de retraso
            dias_retraso = (fecha_actual - prestamo.fecha_max).days
            
            # Verificar si ya existe multa por retraso
            multa_existente = prestamo.multas.filter(tipo='r').first()
            
            if multa_existente:
                # Actualizar monto de la multa existente
                multa_existente.monto = dias_retraso * 1.0
                multa_existente.save()
                multas_actualizadas += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Multa actualizada: Préstamo #{prestamo.id} - ${multa_existente.monto}'
                    )
                )
            else:
                # Crear nueva multa
                Multa.objects.create(
                    prestamo=prestamo,
                    tipo='r',
                    monto=dias_retraso * 1.0,
                    fecha=fecha_actual
                )
                
                # Cambiar estado del préstamo a Multado
                prestamo.estado = 'm'
                prestamo.save()
                
                multas_creadas += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Nueva multa creada: Préstamo #{prestamo.id} - ${dias_retraso}.00'
                    )
                )
        
        # Resumen
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Proceso completado:\n'
                f'   - {multas_creadas} multas creadas\n'
                f'   - {multas_actualizadas} multas actualizadas\n'
                f'   - {prestamos_vencidos.count()} préstamos vencidos revisados'
            )
        )