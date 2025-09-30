from django.db import models
from .slot import Slot
from .event import Event

class ExternalProvidedSlot(Slot):

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


    def __str__(self) -> str:
        return f"{self.start}: {self.discipline} / {self.category_name}"

    @classmethod
    def create_from_jjcm_schedule(cls, slot: dict):

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

            title = f'{slot.get("discipline", "")}: {slot.get("categoryName", "")}'
            
            # competitors = slot.get("competitors", []), # should be a list of Competitor objects
        )
        obj.save()
        print(f"Created ExternalProvidedSlot with hash {slot['hash']}")
        return obj
    
    @classmethod
    def delete_all_not_in_list(cls, hashes: list[str], event: Event):
        cls.objects.filter(event = event).exclude(hash__in=hashes).delete()