from django.db import models
import hashlib
from .competition import Competition
from .competitor import Competitor
from .dojo import Dojo
from .ranks import Rank


class Registration(models.Model):
    """A competitor's registration for a specific competition."""

    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE, related_name='registrations')
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='registrations')
    dojo = models.ForeignKey(Dojo, on_delete=models.RESTRICT, blank=True, null=True, related_name='registrations')

    jjcmRegistrationId = models.IntegerField(unique=True, blank=True, null=True)  # "id" from /registrations
    jjcmAgeClassId = models.IntegerField(blank=True, null=True)
    jjcmWeightClassId = models.IntegerField(blank=True, null=True)
    jjcmRankClassId = models.IntegerField(blank=True, null=True)
    jjcmRankId = models.CharField(max_length=64, blank=True, null=True)  # e.g., ROKKYU, SHODAN

    hash = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        unique_together = ['competitor', 'competition']

    def __str__(self):
        return f"{self.competitor} @ {self.competition}"

    def save(self, *args, **kwargs):
        if not self.hash:
            self.hash = self._compute_hash()
        super().save(*args, **kwargs)

    def _compute_hash(self) -> str:
        data = f"{self.jjcmRegistrationId}:{self.jjcmAgeClassId}:{self.jjcmWeightClassId}:{self.jjcmRankClassId}:{self.jjcmRankId}"
        return hashlib.sha256(data.encode()).hexdigest()

    @classmethod
    def create_from_jjcm(cls, data: dict, competitor: Competitor, competition: Competition, dojo: Dojo = None):
        """Create or update a Registration from JJCM data."""
        registration, created = cls.objects.update_or_create(
            jjcmRegistrationId=data["id"],
            defaults={
                "competitor": competitor,
                "competition": competition,
                "dojo": dojo,
                "jjcmAgeClassId": data.get("age_class_id"),
                "jjcmWeightClassId": data.get("weight_class_id"),
                "jjcmRankClassId": data.get("rank_class_id"),
                "jjcmRankId": data.get("rank_id"),
            }
        )
        if created:
            print(f"Created Registration for {competitor} in {competition}")
        return registration

    @classmethod
    def delete_all_not_in_list(cls, hashes: list[str], competition: Competition):
        cls.objects.filter(competition=competition).exclude(hash__in=hashes).delete()

    @property
    def rank(self):
        """Get the Rank object for this registration's jjcmRankId."""
        if not self.jjcmRankId:
            return None
        try:
            return Rank.objects.get(pk=self.jjcmRankId)
        except Rank.DoesNotExist:
            return None
