from django.db import models


class Competitor(models.Model):
    """A person who competes - stable across competitions."""

    class SexEnum(models.TextChoices):
        FEMALE = 'FEMALE', 'weiblich'
        MALE = 'MALE', 'männlich'

    name = models.CharField(max_length=64)
    givenName = models.CharField(max_length=64)
    sex = models.CharField(max_length=8, blank=True, null=True, choices=SexEnum.choices)

    jjcmCompetitorId = models.IntegerField(unique=True, blank=True, null=True)  # "competitor_id" (same person across competitions)

    def __str__(self):
        return f"{self.givenName} {self.name}"

    @classmethod
    def get_or_create_from_jjcm(cls, data: dict):
        """Get or create a Competitor from JJCM registration data."""
        competitor, created = cls.objects.get_or_create(
            jjcmCompetitorId=data["competitor_id"],
            defaults={
                "name": data["name"],
                "givenName": data["given_name"],
                "sex": data["sex"],
            }
        )
        if created:
            print(f"Created Competitor {data['given_name']} {data['name']}")
        return competitor
