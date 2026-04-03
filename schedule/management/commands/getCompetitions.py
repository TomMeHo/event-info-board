from django.core.management.base import BaseCommand, CommandParser
import os
import requests
from datetime import datetime, timedelta
from schedule.models import Competition


class Command(BaseCommand):
    help = 'Retrieves competitions from the JJ competition manager and creates/updates Competition objects.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--activate',
            type=int,
            metavar='JJCM_ID',
            help='Activate the competition with this JJCM competition ID and deactivate all others'
        )

    def handle(self, *args, **options):
        activate_id = options.get('activate')
        competitions = self.getCompetitions()
        self.stdout.write(self.style.SUCCESS(f"Retrieved {len(competitions)} competitions"))
        self.sync_competitions(competitions, activate_id)

    def sync_competitions(self, competitions: list[dict], activate_id: int = None):
        for comp in competitions:
            competition, created = Competition.objects.update_or_create(
                jjcmCompetitionId=comp['id'],
                defaults={
                    'title': comp['name'],
                    'location': comp.get('city', ''),
                    'firstDay': self.parse_date(comp['date']),
                    'lastDay': self.parse_date(comp['date']) + timedelta(days=1),  # Assume 2-day event
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Competition: {competition.title}"))
            else:
                self.stdout.write(f"Updated Competition: {competition.title}")

        # Handle activation: only one competition can be active
        if activate_id is not None:
            # Deactivate all competitions
            Competition.objects.update(active=False)

            # Activate the specified competition
            activated = Competition.objects.filter(jjcmCompetitionId=activate_id).update(active=True)
            if activated:
                competition = Competition.objects.get(jjcmCompetitionId=activate_id)
                self.stdout.write(self.style.SUCCESS(f"Activated Competition: {competition.title}"))
            else:
                self.stdout.write(self.style.WARNING(f"No competition found with jjcmCompetitionId={activate_id}"))

    def parse_date(self, date_str: str):
        return datetime.strptime(date_str, '%Y-%m-%d').date()

    def getCompetitions(self) -> list[dict]:
        """Fetch competitions from JJCM API.

        Environment variables:
        - JJCM_BASE (optional, default: https://jjcm.foehst.net)
        - JJCM_USERNAME
        - JJCM_PASSWORD
        """
        base = os.getenv('JJCM_BASE', 'https://jjcm.foehst.net')
        login_url = f"{base}/api/auth"
        competitions_url = f"{base}/api/competitions"

        username = os.getenv('JJCM_USERNAME')
        password = os.getenv('JJCM_PASSWORD')
        if not username or not password:
            raise Exception('Please set JJCM_USERNAME and JJCM_PASSWORD environment variables')

        session = requests.Session()

        print("Logging in to JJCM API...")
        try:
            resp = session.post(login_url, json={'username': username, 'password': password}, timeout=10)
        except requests.RequestException as e:
            raise Exception(f"Login request failed: {e}")

        if resp.status_code not in (200, 201, 204):
            try:
                resp = session.post(login_url, data={'username': username, 'password': password}, timeout=10)
            except requests.RequestException as e:
                raise Exception(f"Login request failed (form fallback): {e}")

        if resp.status_code not in (200, 201, 204):
            raise Exception(f"Login failed: {resp.status_code} - {resp.text}")

        print(f"Login successful. Retrieving competitions...")

        try:
            response = session.get(competitions_url, timeout=10)
        except requests.RequestException as e:
            raise Exception(f"Failed to retrieve competitions: {e}")

        if response.status_code != 200:
            raise Exception(f"Failed to retrieve competitions, status code: {response.status_code}, content: {response.text}")

        try:
            return response.json()
        except ValueError as e:
            raise Exception(f"Failed to parse JSON response: {e}")
