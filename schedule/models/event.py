from django.db import models
from datetime import date

class Event(models.Model):

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    location = models.CharField(max_length=200, blank=True)
    firstDay = models.DateField()
    lastDay = models.DateField()

    active = models.BooleanField(default=True)

    jjcmHash = models.CharField(max_length=64, unique=True, blank=True) # sha256 hash of the linked event from JJCM
    jjcmCompetitionId = models.IntegerField(blank=True, null=True)

    # default Meta (no custom app_label) — model will belong to the `schedule` app
    def __str__(self) -> str:
        return str(f"{self.title}")

    def getWeekDaysDE(self) -> dict[str, date]:
        days = {}

        for d in range(self.firstDay.toordinal(), self.lastDay.toordinal() + 1):
            d = date.fromordinal(d)
            wd = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][d.weekday()]
            days[wd] = d

        return days