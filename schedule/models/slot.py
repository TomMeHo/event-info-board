from django.db import models
from .event import Event
from polymorphic.models import PolymorphicModel

class Slot(PolymorphicModel):
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    title = models.CharField(max_length=200, blank=True)

    def displayName(self) -> str:
        # TODO refine
        return self.title

    def __str__(self) -> str:
        return f"{self.start}: {self.displayName()}"
    
    class Meta:
        proxy = False
        verbose_name = "Manually Created Time Slot"
        verbose_name_plural = "Manually Created Time Slots"
