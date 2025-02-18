from django.apps import AppConfig

class MainAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Main_App'  # ✅ Ensure this matches your app's folder name
