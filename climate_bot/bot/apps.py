from django.apps import AppConfig
import threading

class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot'

    def ready(self):
        from . import views
        threading.Thread(target=views.alert_check_loop, daemon=True).start()