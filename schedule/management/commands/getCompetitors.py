from django.core.management.base import BaseCommand, CommandError, CommandParser
import os
import requests
from schedule.models import Competitor, Registration, Dojo, Competition


class Command(BaseCommand):
    help = 'Retrieves the competitors from the JJ competition manager.'

    existingDojoIds = []

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("competition_id", type=int, nargs='?', help="JJCM ID of the competition to retrieve the competitors for. If not provided, uses the active competition.")

    def handle(self, *args, **options):
        competition_id = options.get('competition_id')

        if competition_id:
            competition = Competition.objects.filter(jjcmCompetitionId=competition_id).first()
            if not competition:
                raise CommandError(f'No Competition found with jjcmCompetitionId={competition_id}')
        else:
            competition = Competition.objects.filter(active=True).first()
            if not competition:
                raise CommandError('No active competition found. Please provide a competition_id or set an active competition.')
            competition_id = competition.jjcmCompetitionId

        data = self.getCompetitors(competition_id)
        self.stdout.write(self.style.SUCCESS(f"Retrieved registrations for competition {competition_id}: {len(data)} items"))
        self.save_registrations(data, competition)

    def save_registrations(self, registrations: list[dict], competition: Competition):
        if not registrations:
            print("No registrations to save.")
            return

        saved_registrations = []
        for reg_data in registrations:
            # Get or create Dojo
            dojo = self.get_or_create_dojo(reg_data.get("dojo"))

            # Get or create Competitor (person)
            competitor = Competitor.get_or_create_from_jjcm(reg_data)

            # Create or update Registration (hash computed on save)
            registration = Registration.create_from_jjcm(reg_data, competitor, competition, dojo)
            saved_registrations.append(registration.hash)

        # Clean up old registrations
        Registration.delete_all_not_in_list(saved_registrations, competition)

    def get_or_create_dojo(self, dojo_data: dict) -> Dojo:
        if not dojo_data:
            return None

        dojo_id = dojo_data["id"]

        if dojo_id in self.existingDojoIds:
            return Dojo.objects.get(jjcmDojoId=dojo_id)

        dojo, created = Dojo.objects.get_or_create(
            jjcmDojoId=dojo_id,
            defaults={"name": dojo_data["name"]}
        )
        self.existingDojoIds.append(dojo_id)
        return dojo

    def getCompetitors(cls, eventID: int):
        """Log in to the JJCM API using credentials from environment variables
        and return the registrations JSON for the given event ID.

        Environment variables:
        - JJCM_BASE (optional, default: https://jjcm.foehst.net)
        - JJCM_USERNAME
        - JJCM_PASSWORD
        """
        base = os.getenv('JJCM_BASE', 'https://jjcm.foehst.net')
        login_url = f"{base}/api/auth"
        registrations_url = f"{base}/api/competitions/{eventID}/registrations?rel=dojo"

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

        print(f"Login successful (status {resp.status_code}). Retrieving registrations for event ID: {eventID}")

        try:
            response = session.get(registrations_url, timeout=10)
        except requests.RequestException as e:
            raise Exception(f"Failed to retrieve registrations: {e}")

        if response.status_code != 200:
            raise Exception(f"Failed to retrieve registrations, status code: {response.status_code}, content: {response.text}")

        try:
            return response.json()
        except ValueError as e:
            raise Exception(f"Failed to parse JSON response: {e}")
