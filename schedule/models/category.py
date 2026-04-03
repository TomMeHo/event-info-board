from django.db import models
from .competition import Competition


class Category(models.Model):
    """A competition category from JJCM."""

    class Discipline(models.TextChoices):
        RANDOM_ATTACK = 'RandomAttack', 'Random Attack'
        GROUND_FIGHTING = 'GroundFighting', 'Ground Fighting'
        GROUND_FIGHTING_OPEN = 'GroundFightingOpen', 'Ground Fighting Open'
        PAIRS = 'Pairs', 'Pairs'
        KATA = 'Kata', 'Kata'
        TEAM = 'Team', 'Team'

    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    jjcmCategoryId = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=128)
    discipline = models.CharField(max_length=32, choices=Discipline.choices)

    # Age class info (denormalized for display)
    ageClassName = models.CharField(max_length=64, blank=True, null=True)
    ageClassId = models.IntegerField(blank=True, null=True)
    ageClassMin = models.IntegerField(blank=True, null=True)

    # Weight class info (for ground fighting)
    weightClassName = models.CharField(max_length=64, blank=True, null=True)
    weightClassId = models.IntegerField(blank=True, null=True)

    # Rank class info (for random attack, pairs)
    rankClassName = models.CharField(max_length=64, blank=True, null=True)
    rankClassId = models.IntegerField(blank=True, null=True)

    # Statistics from JJCM
    cardinality = models.IntegerField(default=0, help_text="Number of entries")
    hasGames = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ['competition', 'jjcmCategoryId']
        ordering = ['discipline', 'name']

    def __str__(self):
        return f"{self.get_discipline_display()}: {self.name}"

    @classmethod
    def create_from_jjcm(cls, data: dict, competition: Competition, discipline_key: str):
        """Create or update a Category from JJCM API data.

        Args:
            data: The category wrapper from JJCM API (contains 'category', 'cardinality', etc.)
            competition: The Competition instance
            discipline_key: The discipline key used in the API (e.g., 'random_attack')
        """
        category_data = data.get('category', {})
        jjcm_id = category_data.get('id')

        # Map API discipline key to model choice
        discipline_map = {
            'random_attack': cls.Discipline.RANDOM_ATTACK,
            'ground_fighting': cls.Discipline.GROUND_FIGHTING,
            'ground_fighting_open': cls.Discipline.GROUND_FIGHTING_OPEN,
            'pairs': cls.Discipline.PAIRS,
            'kata': cls.Discipline.KATA,
            'team': cls.Discipline.TEAM,
        }
        discipline = discipline_map.get(discipline_key, discipline_key)

        # Extract age class info
        age_classes = category_data.get('age_class', [])
        age_class = age_classes[0] if age_classes else {}

        # Extract weight class info
        weight_classes = category_data.get('weight_class', [])
        weight_class = weight_classes[0] if weight_classes else {}

        # Extract rank class info
        rank_classes = category_data.get('rank_class', [])
        rank_class = rank_classes[0] if rank_classes else {}

        defaults = {
            'name': data.get('name') or category_data.get('name', ''),
            'discipline': discipline,
            'ageClassName': age_class.get('name'),
            'ageClassId': age_class.get('id'),
            'ageClassMin': age_class.get('min'),
            'weightClassName': weight_class.get('name'),
            'weightClassId': weight_class.get('id'),
            'rankClassName': rank_class.get('name'),
            'rankClassId': rank_class.get('id'),
            'cardinality': data.get('cardinality', 0),
            'hasGames': category_data.get('has_games', False),
        }

        if jjcm_id:
            category, created = cls.objects.update_or_create(
                competition=competition,
                jjcmCategoryId=jjcm_id,
                defaults=defaults
            )
        else:
            # Categories without ID - match by name and discipline
            category, created = cls.objects.update_or_create(
                competition=competition,
                discipline=discipline,
                name=defaults['name'],
                jjcmCategoryId__isnull=True,
                defaults=defaults
            )

        return category, created

    @classmethod
    def delete_stale(cls, competition: Competition, discipline: str, current_ids: list):
        """Delete categories that are no longer in the API response."""
        cls.objects.filter(
            competition=competition,
            discipline=discipline
        ).exclude(
            jjcmCategoryId__in=[i for i in current_ids if i]
        ).exclude(
            jjcmCategoryId__isnull=False
        ).delete()
