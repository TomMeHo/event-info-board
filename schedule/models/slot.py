from django.db import models
from .competition import Competition
from polymorphic.models import PolymorphicModel


class Slot(PolymorphicModel):
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)

    title = models.CharField(max_length=200, blank=True)
    show_on_detail = models.BooleanField(default=True)

    def displayName(self) -> str:
        return self.title

    def __str__(self) -> str:
        return f"{self.start}: {self.displayName()}"

    class Meta:
        proxy = False
        verbose_name = "Manually Created Time Slot"
        verbose_name_plural = "Manually Created Time Slots"
