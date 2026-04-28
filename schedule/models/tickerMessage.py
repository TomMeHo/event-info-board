from django.db import models
from .competition import Competition


class TickerMessage(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    highlighted = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Ticker Message"
        verbose_name_plural = "Ticker Messages"

    def __str__(self):
        return self.text
