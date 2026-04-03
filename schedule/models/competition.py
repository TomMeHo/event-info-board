from django.db import models
from datetime import date


class Competition(models.Model):

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    location = models.CharField(max_length=200, blank=True)
    firstDay = models.DateField()
    lastDay = models.DateField()

    active = models.BooleanField(default=True)

    jjcmHash = models.CharField(max_length=64, blank=True, null=True)  # sha256 hash of the schedule from JJCM
    jjcmEntriesHash = models.CharField(max_length=64, blank=True, null=True)  # sha256 hash of entries
    jjcmCategoriesHash = models.CharField(max_length=64, blank=True, null=True)  # sha256 hash of categories
    jjcmCompetitionId = models.IntegerField(blank=True, null=True, unique=True)

    class Meta:
        db_table = 'schedule_event'  # Keep existing table name to avoid data migration

    def __str__(self) -> str:
        return str(f"{self.title}")

    def getWeekDaysDE(self) -> dict[str, date]:
        days = {}

        for d in range(self.firstDay.toordinal(), self.lastDay.toordinal() + 1):
            d = date.fromordinal(d)
            wd = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][d.weekday()]
            days[wd] = d

        return days
