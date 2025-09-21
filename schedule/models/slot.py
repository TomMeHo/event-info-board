from django.db import models
from .event import Event


class Slot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)
    external_id = models.TextField(max_length=128, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    def __str__(self) -> str:
        return f"{self.start_time} - {self.end_time}: {self.title}"
   