from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


def verificar_prestamos_job():
    """Job que ejecuta el comando de verificación de préstamos vencidos"""
    try:
        logger.info("Ejecutando verificación de préstamos vencidos...")
        call_command('verificar_prestamos_vencidos')
        logger.info("Verificación completada exitosamente")
    except Exception as e:
        logger.error(f"Error al ejecutar verificación: {str(e)}")


def start_scheduler():
    """Inicia el scheduler en segundo plano"""
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Programar job para ejecutarse todos los días a las 9:00 AM
    scheduler.add_job(
        verificar_prestamos_job,
        'cron',
        hour=9,
        minute=0,
        id='verificar_prestamos_vencidos',
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("✅ Scheduler iniciado - verificación programada para las 9:00 AM todos los días")
    print("✅ Scheduler iniciado - verificación programada para las 9:00 AM todos los días")