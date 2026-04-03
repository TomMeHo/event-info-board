from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, datetime, timedelta

from .models import (
    Competition, Competitor, Registration, Dojo, Rank,
    Slot, ExternalProvidedSlot, Category,
    Entry, SingleCompetitorEntry, PairsEntry, KataEntry, TeamEntry
)


class CompetitionModelTest(TestCase):
    def setUp(self):
        self.competition = Competition.objects.create(
            title="Test Competition",
            description="A test competition",
            location="Test Location",
            firstDay=date(2026, 5, 9),
            lastDay=date(2026, 5, 10),
            active=True,
            jjcmCompetitionId=99
        )

    def test_str(self):
        self.assertEqual(str(self.competition), "Test Competition")

    def test_get_week_days_de(self):
        days = self.competition.getWeekDaysDE()
        self.assertIn("Samstag", days)
        self.assertIn("Sonntag", days)
        self.assertEqual(days["Samstag"], date(2026, 5, 9))
        self.assertEqual(days["Sonntag"], date(2026, 5, 10))

    def test_active_default(self):
        comp = Competition.objects.create(
            title="Another Competition",
            firstDay=date(2026, 6, 1),
            lastDay=date(2026, 6, 1),
        )
        self.assertTrue(comp.active)


class CompetitorModelTest(TestCase):
    def setUp(self):
        self.competitor = Competitor.objects.create(
            name="Müller",
            givenName="Max",
            sex="MALE",
            jjcmCompetitorId=123
        )

    def test_str(self):
        self.assertEqual(str(self.competitor), "Max Müller")


class DojoModelTest(TestCase):
    def setUp(self):
        self.dojo = Dojo.objects.create(
            name="Test Dojo",
            jjcmDojoId=42
        )

    def test_fields(self):
        self.assertEqual(self.dojo.name, "Test Dojo")
        self.assertEqual(self.dojo.jjcmDojoId, 42)


class RankModelTest(TestCase):
    def setUp(self):
        self.rank_kyu = Rank.objects.create(
            ID="ROKKYU",
            name="6. Kyu (Rokkyu)",
            color="grün",
            rankClass="Kyu-Grad",
            kyu=6
        )
        self.rank_dan = Rank.objects.create(
            ID="SHODAN",
            name="1. Dan (Shodan)",
            color="schwarz",
            rankClass="Dan-Grad",
            dan=1
        )
        self.rank_brown_stripe = Rank.objects.create(
            ID="IKKYU",
            name="1. Kyu (Ikkyu)",
            color="braun mit 3 Streifen",
            rankClass="Kyu-Grad",
            kyu=1
        )

    def test_str(self):
        self.assertEqual(str(self.rank_kyu), "6. Kyu (Rokkyu)")

    def test_get_belt_css_class(self):
        self.assertEqual(self.rank_kyu.get_belt_css_class(), "belt-green")
        self.assertEqual(self.rank_dan.get_belt_css_class(), "belt-black")
        self.assertEqual(self.rank_brown_stripe.get_belt_css_class(), "belt-brown-3stripe")

    def test_get_belt_html_contains_class(self):
        html = self.rank_kyu.get_belt_html()
        self.assertIn("belt-green", html)
        self.assertIn("<span", html)

    def test_get_belt_html_dan_stripes(self):
        html = self.rank_dan.get_belt_html()
        self.assertIn("belt-stripe-yellow", html)

    def test_get_belt_html_brown_stripes(self):
        html = self.rank_brown_stripe.get_belt_html()
        # Should have 3 stripes
        self.assertEqual(html.count("belt-stripe"), 3)

    def test_get_display_html(self):
        html = self.rank_kyu.get_display_html()
        self.assertIn("6. Kyu (Rokkyu)", html)
        self.assertIn("belt-green", html)


class RegistrationModelTest(TestCase):
    def setUp(self):
        self.competition = Competition.objects.create(
            title="Test Competition",
            firstDay=date(2026, 5, 9),
            lastDay=date(2026, 5, 10),
        )
        self.competitor = Competitor.objects.create(
            name="Test",
            givenName="Person",
            jjcmCompetitorId=1
        )
        self.dojo = Dojo.objects.create(name="Test Dojo", jjcmDojoId=1)
        self.rank = Rank.objects.create(
            ID="ROKKYU",
            name="6. Kyu",
            color="grün",
            kyu=6
        )
        self.registration = Registration.objects.create(
            competitor=self.competitor,
            competition=self.competition,
            dojo=self.dojo,
            jjcmRegistrationId=100,
            jjcmRankId="ROKKYU"
        )

    def test_str(self):
        self.assertEqual(str(self.registration), "Person Test @ Test Competition")

    def test_rank_property(self):
        self.assertEqual(self.registration.rank, self.rank)

    def test_rank_property_none(self):
        self.registration.jjcmRankId = "INVALID"
        self.registration.save()
        self.assertIsNone(self.registration.rank)


class SlotModelTest(TestCase):
    def setUp(self):
        self.competition = Competition.objects.create(
            title="Test Competition",
            firstDay=date(2026, 5, 9),
            lastDay=date(2026, 5, 10),
        )
        self.slot = ExternalProvidedSlot.objects.create(
            competition=self.competition,
            title="Test Slot",
            start=datetime(2026, 5, 9, 10, 0),
            end=datetime(2026, 5, 9, 11, 0),
            discipline="RandomAttack",
            category_name="Erwachsene, grün",
            type="pre",
            tatami=1
        )

    def test_str(self):
        # ExternalProvidedSlot __str__ includes discipline and category_name
        self.assertIn("RandomAttack", str(self.slot))
        self.assertIn("Erwachsene, grün", str(self.slot))

    def test_hash_computed_on_save(self):
        self.assertIsNotNone(self.slot.hash)
        self.assertEqual(len(self.slot.hash), 64)  # SHA256 hex


class CategoryModelTest(TestCase):
    def setUp(self):
        self.competition = Competition.objects.create(
            title="Test Competition",
            firstDay=date(2026, 5, 9),
            lastDay=date(2026, 5, 10),
        )
        self.category = Category.objects.create(
            competition=self.competition,
            name="Erwachsene, grün",
            discipline=Category.Discipline.RANDOM_ATTACK,
            jjcmCategoryId=100,
            cardinality=5
        )

    def test_str(self):
        self.assertEqual(str(self.category), "Random Attack: Erwachsene, grün")


class EntryModelTest(TestCase):
    def setUp(self):
        self.competition = Competition.objects.create(
            title="Test Competition",
            firstDay=date(2026, 5, 9),
            lastDay=date(2026, 5, 10),
        )
        self.competitor = Competitor.objects.create(
            name="Test",
            givenName="Person",
            jjcmCompetitorId=1
        )
        self.registration = Registration.objects.create(
            competitor=self.competitor,
            competition=self.competition,
            jjcmRegistrationId=100
        )
        self.category = Category.objects.create(
            competition=self.competition,
            name="Test Category",
            discipline=Category.Discipline.RANDOM_ATTACK
        )

    def test_single_competitor_entry(self):
        entry = SingleCompetitorEntry.objects.create(
            competition=self.competition,
            jjcmEntryId=1,
            discipline=SingleCompetitorEntry.Discipline.RANDOM_ATTACK,
            competitor=self.registration,
            category=self.category
        )
        self.assertEqual(entry.get_discipline_display_name(), "Random Attack")

    def test_pairs_entry(self):
        competitor2 = Competitor.objects.create(
            name="Partner",
            givenName="Test",
            jjcmCompetitorId=2
        )
        registration2 = Registration.objects.create(
            competitor=competitor2,
            competition=self.competition,
            jjcmRegistrationId=101
        )
        entry = PairsEntry.objects.create(
            competition=self.competition,
            jjcmEntryId=2,
            competitor_a=self.registration,
            competitor_b=registration2
        )
        self.assertEqual(entry.get_discipline_display_name(), "Paare")

    def test_kata_entry(self):
        competitor2 = Competitor.objects.create(
            name="Uke",
            givenName="Test",
            jjcmCompetitorId=3
        )
        registration2 = Registration.objects.create(
            competitor=competitor2,
            competition=self.competition,
            jjcmRegistrationId=102
        )
        entry = KataEntry.objects.create(
            competition=self.competition,
            jjcmEntryId=3,
            tori=self.registration,
            uke=registration2
        )
        self.assertEqual(entry.get_discipline_display_name(), "Kata")

    def test_team_entry(self):
        entry = TeamEntry.objects.create(
            competition=self.competition,
            jjcmEntryId=4
        )
        entry.members.add(self.registration)
        self.assertEqual(entry.get_discipline_display_name(), "Team")
        self.assertEqual(entry.members.count(), 1)


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.competition = Competition.objects.create(
            title="Test Competition",
            firstDay=date(2026, 5, 9),
            lastDay=date(2026, 5, 10),
            active=True,
            jjcmCompetitionId=99
        )
        self.competitor = Competitor.objects.create(
            name="Test",
            givenName="Person",
            jjcmCompetitorId=1
        )
        self.dojo = Dojo.objects.create(name="Test Dojo", jjcmDojoId=1)
        self.registration = Registration.objects.create(
            competitor=self.competitor,
            competition=self.competition,
            dojo=self.dojo,
            jjcmRegistrationId=100
        )
        self.slot = ExternalProvidedSlot.objects.create(
            competition=self.competition,
            title="Test Slot",
            start=datetime(2026, 5, 9, 10, 0),
            end=datetime(2026, 5, 9, 11, 0),
            discipline="RandomAttack",
            category_name="Test Category",
            type="pre",
            tatami=1
        )

    def test_registrations_list_view(self):
        response = self.client.get(reverse('registrations_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test")
        self.assertContains(response, "Person")

    def test_registrations_list_search(self):
        response = self.client.get(reverse('registrations_list'), {'search': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Person")

    def test_registrations_list_dojo_filter(self):
        response = self.client.get(reverse('registrations_list'), {'dojo': self.dojo.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Dojo")

    def test_registration_detail_view(self):
        response = self.client.get(reverse('registration_detail', args=[self.registration.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Person")
        self.assertContains(response, "Test")

    def test_registration_detail_404(self):
        response = self.client.get(reverse('registration_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_schedule_compact_view(self):
        response = self.client.get(reverse('schedule_compact'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Zeitplan")

    def test_slot_detail_view(self):
        response = self.client.get(reverse('slot_detail', args=[self.slot.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "RandomAttack")

    def test_slot_detail_404(self):
        response = self.client.get(reverse('slot_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_event_board_view(self):
        response = self.client.get(reverse('event_board'))
        self.assertEqual(response.status_code, 200)


class ViewsNoCompetitionTest(TestCase):
    """Test views when no active competition exists."""

    def setUp(self):
        self.client = Client()

    def test_registrations_list_no_competition(self):
        response = self.client.get(reverse('registrations_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kein Wettkampf ausgewählt")

    def test_schedule_compact_no_competition(self):
        response = self.client.get(reverse('schedule_compact'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kein Wettkampf ausgewählt")

    def test_event_board_no_competition(self):
        response = self.client.get(reverse('event_board'))
        self.assertEqual(response.status_code, 200)
