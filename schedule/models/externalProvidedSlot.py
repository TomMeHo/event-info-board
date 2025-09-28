from django.db import models
from .slot import Slot

class ExternalProvidedSlot(Slot):

    #TODO add hash to identify changes

    hash = models.CharField(max_length=64, unique=True, blank=True) # sha256 hash of the original slot data from JJCM
    discipline = models.CharField(max_length=200, blank=True)
    category_name = models.CharField(max_length=200, blank=True)
    type = models.CharField(max_length=20, blank=True) # pre or final
    tatami = models.IntegerField(blank=True, null=True)

    #TODO add competitors from slot competitors array

    class Meta:
        proxy = False
        verbose_name = "Externally Provided Time Slot"
        verbose_name_plural = "Externally Provided Time Slots"

    @classmethod
    def createFromJjcmSchedule(cls, slot: dict):

        if cls.objects.filter(hash=slot["hash"]).exists():
            print(f"Slot with hash {slot['hash']} already exists, skipping.")
            return cls.objects.get(hash=slot["hash"])

        obj = ExternalProvidedSlot(
            start = slot["start"],
            end = slot["end"],
            event = slot["event"],

            hash = slot["hash"],
            
            discipline = slot.get("discipline", ""),
            category_name = slot.get("categoryName", ""),
            type = slot.get("type", ""),
            tatami = slot["tatami"],
            
            # competitors = slot.get("competitors", []), # should be a list of Competitor objects
        )
        obj.save()
        print(f"Created ExternalProvidedSlot with hash {slot['hash']}")
        return obj