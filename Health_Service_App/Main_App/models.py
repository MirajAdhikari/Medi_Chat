from django.db import models

class MedicalImage(models.Model):
    image = models.ImageField(upload_to='uploads/')
    diagnosis = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
