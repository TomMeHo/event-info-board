from django.db import models
import hashlib
from .slot import Slot
from .competition import Competition
from .registration import Registration


class ExternalProvidedSlot(Slot):

    hash = models.CharField(max_length=64, unique=True, blank=True)  # sha256 hash of the original slot data from JJCM
    discipline = models.CharField(max_length=200, blank=True)
    category_name = models.CharField(max_length=200, blank=True)
    type = models.CharField(max_length=20, blank=True)  # pre or final
    tatami = models.IntegerField(blank=True, null=True)

    registrations = models.ManyToManyField(Registration, blank=True, related_name='slots')

    class Meta:
        proxy = False
        verbose_name = "Externally Provided Time Slot"
        verbose_name_plural = "Externally Provided Time Slots"

    def __str__(self) -> str:
        return f"{self.start}: {self.discipline} / {self.category_name}"

    def save(self, *args, **kwargs):
        if not self.hash:
            self.hash = self._compute_hash()
        super().save(*args, **kwargs)

    def _compute_hash(self) -> str:
        data = f"{self.start}:{self.end}:{self.discipline}:{self.category_name}:{self.type}:{self.tatami}"
        return hashlib.sha256(data.encode()).hexdigest()

    @classmethod
    def create_from_jjcm_schedule(cls, slot: dict):
        # Compute hash from slot data to check for duplicates
        start = slot["start"]
        end = slot["end"]
        discipline = cls.replaceTextPatterns(slot.get("discipline", ""))
        category_name = cls.replaceTextPatterns(slot.get("categoryName", ""))
        slot_type = slot.get("type", "")
        tatami = slot["tatami"]

        slot_hash = hashlib.sha256(
            f"{start}:{end}:{discipline}:{category_name}:{slot_type}:{tatami}".encode()
        ).hexdigest()

        if cls.objects.filter(hash=slot_hash).exists():
            print(f"Slot with hash {slot_hash} already exists, skipping.")
            return cls.objects.get(hash=slot_hash)

        obj = ExternalProvidedSlot(
            start=start,
            end=end,
            competition=slot["competition"],
            hash=slot_hash,
            discipline=discipline,
            category_name=category_name,
            type=slot_type,
            tatami=tatami,
            title=f'{slot.get("discipline", "")}: {slot.get("categoryName", "")}'
        )
        obj.save()

        # Link registrations via their jjcmRegistrationId
        registration_ids = slot.get("competitors", [])
        if registration_ids:
            registrations = Registration.objects.filter(jjcmRegistrationId__in=registration_ids)
            obj.registrations.set(registrations)

        print(f"Created ExternalProvidedSlot with hash {slot_hash}")
        return obj

    @classmethod
    def delete_all_not_in_list(cls, hashes: list[str], competition: Competition):
        cls.objects.filter(competition=competition).exclude(hash__in=hashes).delete()

    @classmethod
    def replaceTextPatterns(cls, txt: str) -> str:
        txt = txt.replace("RandomAttack", "Random Attack")
        txt = txt.replace("GroundFightingOpen", "Bodenkampf, offene Klasse")
        txt = txt.replace("GroundFighting", "Bodenkampf")
        txt = txt.replace("MALE", "Männer")
        txt = txt.replace("FEMALE", "Frauen")
        return txt
