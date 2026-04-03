from django.db import models
from polymorphic.models import PolymorphicModel
from .competition import Competition
from .registration import Registration
from .dojo import Dojo
from .category import Category


class Entry(PolymorphicModel):
    """Base class for competition entries (discipline registrations)."""

    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    dojo = models.ForeignKey(
        Dojo,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='entries'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='entries'
    )
    jjcmEntryId = models.IntegerField(unique=True)
    overrideCategoryId = models.IntegerField(blank=True, null=True)
    result = models.CharField(max_length=64, blank=True, null=True, help_text="Competition result (e.g., 1st, 2nd, 3rd)")

    class Meta:
        verbose_name_plural = "Entries"

    def __str__(self):
        return f"Entry {self.jjcmEntryId}"

    def get_discipline_display_name(self):
        """Return a human-readable discipline name."""
        return "Entry"


class SingleCompetitorEntry(Entry):
    """Entry for disciplines with a single competitor (RandomAttack, GroundFighting, GroundFightingOpen)."""

    class Discipline(models.TextChoices):
        RANDOM_ATTACK = 'RandomAttack', 'Random Attack'
        GROUND_FIGHTING = 'GroundFighting', 'Ground Fighting'
        GROUND_FIGHTING_OPEN = 'GroundFightingOpen', 'Ground Fighting Open'

    discipline = models.CharField(max_length=32, choices=Discipline.choices)
    competitor = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name='single_entries'
    )

    def __str__(self):
        return f"{self.get_discipline_display()}: {self.competitor}"

    def get_discipline_display_name(self):
        """Return a human-readable discipline name."""
        return self.get_discipline_display()

    @classmethod
    def create_from_jjcm(cls, data: dict, competition: Competition, discipline_key: str, dojo: Dojo = None):
        """Create or update from JJCM API data."""
        from .registration import Registration

        discipline_map = {
            'random_attack': cls.Discipline.RANDOM_ATTACK,
            'ground_fighting': cls.Discipline.GROUND_FIGHTING,
            'ground_fighting_open': cls.Discipline.GROUND_FIGHTING_OPEN,
        }

        competitor_reg = Registration.objects.filter(
            jjcmRegistrationId=data.get('competitor_registration_id')
        ).first()

        entry, created = cls.objects.update_or_create(
            jjcmEntryId=data['id'],
            defaults={
                'competition': competition,
                'dojo': dojo,
                'discipline': discipline_map.get(discipline_key),
                'competitor': competitor_reg,
                'overrideCategoryId': data.get('override_category_id'),
            }
        )
        return entry, created


class PairsEntry(Entry):
    """Entry for Pairs discipline (two competitors)."""

    competitor_a = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name='pairs_entries_as_a'
    )
    competitor_b = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name='pairs_entries_as_b'
    )

    class Meta:
        verbose_name_plural = "Pairs Entries"

    def __str__(self):
        return f"Pairs: {self.competitor_a} & {self.competitor_b}"

    def get_discipline_display_name(self):
        """Return a human-readable discipline name."""
        return "Paare"

    @classmethod
    def create_from_jjcm(cls, data: dict, competition: Competition, dojo: Dojo = None):
        """Create or update from JJCM API data."""
        from .registration import Registration

        competitor_a = Registration.objects.filter(
            jjcmRegistrationId=data.get('competitor_a_registration_id')
        ).first()
        competitor_b = Registration.objects.filter(
            jjcmRegistrationId=data.get('competitor_b_registration_id')
        ).first()

        entry, created = cls.objects.update_or_create(
            jjcmEntryId=data['id'],
            defaults={
                'competition': competition,
                'dojo': dojo,
                'competitor_a': competitor_a,
                'competitor_b': competitor_b,
                'overrideCategoryId': data.get('override_category_id'),
            }
        )
        return entry, created


class KataEntry(Entry):
    """Entry for Kata discipline (tori and uke)."""

    tori = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name='kata_entries_as_tori'
    )
    uke = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name='kata_entries_as_uke'
    )

    class Meta:
        verbose_name_plural = "Kata Entries"

    def __str__(self):
        return f"Kata: {self.tori} (tori) & {self.uke} (uke)"

    def get_discipline_display_name(self):
        """Return a human-readable discipline name."""
        return "Kata"

    @classmethod
    def create_from_jjcm(cls, data: dict, competition: Competition, dojo: Dojo = None):
        """Create or update from JJCM API data."""
        from .registration import Registration

        tori = Registration.objects.filter(
            jjcmRegistrationId=data.get('tori_registration_id')
        ).first()
        uke = Registration.objects.filter(
            jjcmRegistrationId=data.get('uke_registration_id')
        ).first()

        entry, created = cls.objects.update_or_create(
            jjcmEntryId=data['id'],
            defaults={
                'competition': competition,
                'dojo': dojo,
                'tori': tori,
                'uke': uke,
                'overrideCategoryId': data.get('override_category_id'),
            }
        )
        return entry, created


class TeamEntry(Entry):
    """Entry for Team discipline (multiple members)."""

    members = models.ManyToManyField(
        Registration,
        related_name='team_entries'
    )
    comment = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Team Entries"

    def __str__(self):
        return f"Team: {self.dojo.name if self.dojo else 'Unknown'} ({self.members.count()} members)"

    def get_discipline_display_name(self):
        """Return a human-readable discipline name."""
        return "Team"

    @classmethod
    def create_from_jjcm(cls, data: dict, competition: Competition, dojo: Dojo = None, members_data: list = None):
        """Create or update from JJCM API data."""
        from .registration import Registration

        entry, created = cls.objects.update_or_create(
            jjcmEntryId=data['id'],
            defaults={
                'competition': competition,
                'dojo': dojo,
                'comment': data.get('comment'),
                'overrideCategoryId': data.get('override_category_id'),
            }
        )

        # Update members
        if members_data:
            member_ids = [m.get('id') for m in members_data]
            members = Registration.objects.filter(jjcmRegistrationId__in=member_ids)
            entry.members.set(members)

        return entry, created
