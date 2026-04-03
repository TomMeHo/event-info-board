from datetime import datetime, timedelta, time
import hashlib
import os
from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError, CommandParser
from requests import get
from schedule.models import Competition, ExternalProvidedSlot



class Command(BaseCommand):
    TIME_OFFSET_START = time(9)
    help = 'Retrieves the schedule from the JJ competition manager.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("competition_id", type=int, nargs='?', help="JJCM ID of the competition to retrieve the schedule for. If not provided, retrieves for all active competitions.")

    def handle(self, *args, **options):
        competition_id = options.get("competition_id")
        competitions = [competition_id] if competition_id else Competition.objects.filter(active=True).filter(~Q(jjcmCompetitionId=None)).values_list('jjcmCompetitionId', flat=True)

        for comp_id in competitions:
            try:
                schedule = Command.getSchedule(comp_id)
            except Exception as e:
                raise CommandError(f'Error retrieving schedule for competition {comp_id}: {e}')

            competition = Competition.objects.get(jjcmCompetitionId=comp_id)
            schedule_hash = hashlib.sha256(str(schedule).encode()).hexdigest()

            if competition.jjcmHash != schedule_hash:
                print(f"Schedule for competition {competition} has changed, updating...")

                slot_hashes = self._enrich_and_save_slots(schedule, competition)
                ExternalProvidedSlot.delete_all_not_in_list(slot_hashes, competition)

                competition.jjcmHash = schedule_hash
                competition.save()
            else:
                print(f"Schedule for competition '{competition}' has not changed, skipping.")

            print(f"Successfully retrieved schedule for competition: {comp_id} / '{competition}'")

    def _enrich_and_save_slots(self, schedule, competition) -> list[str]:
        hashes = []
        if not schedule:
            print(f"No schedule data available for competition {competition}.")
            return hashes

        for day_entry in schedule:
            weekdays = competition.getWeekDaysDE()
            weekday = day_entry["day"]
            if weekday not in weekdays:
                print(f"Wochentag '{weekday}' kommt nicht im aktiven Event vor. Start und Ende prüfen bzw. referenziertes JJCM-Event.")
            else:
                date = competition.getWeekDaysDE()[day_entry["day"]]
                print(f"Processing schedule for date: {date}")

                tatami_number = 0

                for tatami in day_entry["tatami"]:
                    tatami_number += 1
                    nine_o_clock = datetime.combine(date, self.TIME_OFFSET_START)

                    for slot in tatami["items"]:
                        if "id" in slot and slot["id"][:5] == "pause":
                            continue  # skip breaks

                        slot["start"] = nine_o_clock + timedelta(minutes=slot["begin"])
                        slot["end"] = slot["start"] + timedelta(minutes=slot["duration"])
                        slot["competition"] = competition
                        slot["tatami"] = tatami_number

                        # Create slot (hash computed by model on save)
                        saved_slot = ExternalProvidedSlot.create_from_jjcm_schedule(slot)
                        hashes.append(saved_slot.hash)

        return hashes

    @classmethod
    def getSchedule(cls, competitionID: int):
        print(f"Retrieving schedule for competition ID: {competitionID}")

        base = os.getenv('JJCM_BASE', 'https://jjcm.foehst.net')
        uri = f"{base}/api/competitions/{competitionID}/schedule"
        response = get(uri, timeout=10)
        if response.status_code == 404:
            print(f"No schedule found for competition {competitionID} (404).")
            return None
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve schedule, status code: {response.status_code}, content: {response.text}")
        try:
            return response.json()
        except ValueError as e:
            raise Exception(f"Failed to parse JSON response: {e}")
