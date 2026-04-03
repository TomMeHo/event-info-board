from django.db import models

class Dojo(models.Model):
    
    name = models.CharField(max_length=128)
    jjcmDojoId = models.IntegerField(blank=True, null=True)
