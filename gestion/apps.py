from django.apps import AppConfig

class GestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion'

    def ready(self):
        """Se ejecuta cuando Django inicia"""
        import os
        
        # Solo iniciar scheduler en el proceso principal
        # (no en migraciones, tests, etc.)
        if os.environ.get('RUN_MAIN') == 'true':
            from gestion import scheduler
            scheduler.start_scheduler()