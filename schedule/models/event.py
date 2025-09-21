from django.db import models

class Event(models.Model):
    date = models.DateField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)

    # default Meta (no custom app_label) — model will belong to the `schedule` app
    def __str__(self) -> str:
        return str(f"{self.date}: {self.title}")