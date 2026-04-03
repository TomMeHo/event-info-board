from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class Rank(models.Model):

    class ObiColor(models.TextChoices):
        WHITE = 'weiß'
        WHITE_YELLOW = 'weiß-gelb'
        YELLOW = 'gelb'
        WHITE_ORANGE = 'weiß-orange'
        ORANGE = 'orange'
        WHITE_GREEN = 'weiß-grün'
        GREEN = 'grün'
        WHITE_BLUE = 'weiß-blau'
        BLUE = 'blau'
        BROWN = 'braun'
        BROWN_1STRIPE = 'braun mit 1 Streifen'
        BROWN_2STRIPE = 'braun mit 2 Streifen'
        BROWN_3STRIPE = 'braun mit 3 Streifen'
        BLACK = 'schwarz'
        RED_WHITE = 'rot-weiß'
        RED = 'rot'

    class RankClass(models.TextChoices):
        MON = 'Mon-Grad'
        KYU = 'Kyu-Grad'
        DAN = 'Dan-Grad'

    # CSS class mapping for belt colors
    BELT_CSS_CLASS = {
        'weiß': 'belt-white',
        'weiß-gelb': 'belt-white-yellow',
        'gelb': 'belt-yellow',
        'weiß-orange': 'belt-white-orange',
        'orange': 'belt-orange',
        'weiß-grün': 'belt-white-green',
        'grün': 'belt-green',
        'weiß-blau': 'belt-white-blue',
        'blau': 'belt-blue',
        'braun': 'belt-brown',
        'braun mit 1 Streifen': 'belt-brown-1stripe',
        'braun mit 2 Streifen': 'belt-brown-2stripe',
        'braun mit 3 Streifen': 'belt-brown-3stripe',
        'schwarz': 'belt-black',
        'rot-weiß': 'belt-red-white',
        'rot': 'belt-red',
    }

    ID = models.CharField(verbose_name='Rang', primary_key=True, max_length=64)
    name = models.CharField(max_length=32)
    color = models.CharField(max_length=24, blank=True, null=True, choices=ObiColor.choices)
    rankClass = models.CharField(max_length=16, blank=True, null=True, choices=RankClass.choices)
    mon = models.IntegerField(blank=True, null=True)
    kyu = models.IntegerField(blank=True, null=True)
    dan = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_belt_css_class(self):
        """Return the CSS class for the belt color."""
        return self.BELT_CSS_CLASS.get(self.color, '')

    def get_belt_html(self, float_end=False):
        """Generate HTML for the belt display including stripes."""
        if not self.color:
            return self.name or '-'

        belt_class = self.get_belt_css_class()
        float_class = ' float-end' if float_end else ''

        stripes_html = ''
        # Generate center stripe for white-X Mon belts
        if self.color == 'weiß-gelb':
            stripes_html = '<span class="belt-center-stripe belt-center-stripe-yellow"></span>'
        elif self.color == 'weiß-orange':
            stripes_html = '<span class="belt-center-stripe belt-center-stripe-orange"></span>'
        elif self.color == 'weiß-grün':
            stripes_html = '<span class="belt-center-stripe belt-center-stripe-green"></span>'
        elif self.color == 'weiß-blau':
            stripes_html = '<span class="belt-center-stripe belt-center-stripe-blue"></span>'
        # Generate stripes for brown belts with stripes (red stripes)
        elif self.color == 'braun mit 1 Streifen':
            stripes_html = '<span class="belt-stripe" style="right: 8px;"></span>'
        elif self.color == 'braun mit 2 Streifen':
            stripes_html = '<span class="belt-stripe" style="right: 8px;"></span><span class="belt-stripe" style="right: 16px;"></span>'
        elif self.color == 'braun mit 3 Streifen':
            stripes_html = '<span class="belt-stripe" style="right: 8px;"></span><span class="belt-stripe" style="right: 16px;"></span><span class="belt-stripe" style="right: 24px;"></span>'
        # Generate stripes for Dan grades (1-5 get yellow stripes)
        elif self.dan and 1 <= self.dan <= 5:
            stripes = []
            for i in range(self.dan):
                pos = 8 + (i * 8)
                stripes.append(f'<span class="belt-stripe-yellow" style="right: {pos}px;"></span>')
            stripes_html = ''.join(stripes)

        belt_html = f'<span class="belt {belt_class}{float_class}">{stripes_html}</span>'
        return mark_safe(belt_html)

    def get_display_html(self, float_end=False):
        """Generate full display HTML with name and belt symbol."""
        name = self.name or '-'
        belt = self.get_belt_html(float_end=float_end)
        return mark_safe(f'{name} {belt}')
