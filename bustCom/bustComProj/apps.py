from django.apps import AppConfig

class BustComProjConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bustComProj'

    def ready(self):
        import bustComProj.signals  
