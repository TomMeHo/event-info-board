from datetime import datetime, timedelta, time
import hashlib
from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError, CommandParser
from requests import get
from schedule.models import Event, externalProvidedSlot as eps



class Command(BaseCommand):
    TIME_OFFSET_START = time(9)
    help = 'Retrieves the schedule from the JJ competition manager.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("event_id", type=int, nargs='?', help="ID of the event to retrieve the schedule for. If not provided, retrieves for all active events.")

    def handle(self, *args, **options):
        event_id = options.get("event_id")
        events = [ event_id ] if (event_id) else Event.objects.filter(active=True).filter(~Q(jjcmCompetitionId=None)).values_list('jjcmCompetitionId', flat=True)

        for eventId in events:
            try:
                schedule = Command.getSchedule(eventId)
            except Exception as e:
                raise CommandError(f'Error retrieving schedule for event {eventId}: {e}')
            
            event_object = Event.objects.get(jjcmCompetitionId=eventId)
            event_hash = hashlib.sha256( str(schedule).encode()).hexdigest()
            
            if event_object.jjcmHash != event_hash:
                print(f"Schedule for event {event_object} has changed, updating...")

                slot_hashes = self._enrich_and_save_slots(schedule, event_object)
                eps.ExternalProvidedSlot.delete_all_not_in_list(slot_hashes, event_object)

                event_object.jjcmHash = event_hash
                event_object.save()
            else:
                print(f"Schedule for event '{event_object}' has not changed, skipping.")
            
            # Placeholder for actual schedule retrieval logic
            print(f"Successfully retrieved schedule for event: {eventId} / '{event_object}'")

    def _enrich_and_save_slots(self, schedule, event_object) -> list[str]:
        hashes = []
        for day_entry in schedule:
            weekdays = event_object.getWeekDaysDE()
            weekday = day_entry["day"]
            if weekday not in weekdays:
                print(f"Wochentag '{ weekday }' kommt nicht im aktiven Event vor. Start und Ende prüfen bzw. referenziertes JJCM-Event.")
            else:
                date = event_object.getWeekDaysDE()[day_entry["day"]]
                print(f"Processing schedule for date: {date}")

                tatami_number = 0

                for tatami in day_entry["tatami"]:
                    tatami_number += 1
                    tatami_begin = tatami["begin"] # start time on this tatami, offset to 9 AM
                    tatami_start_time = datetime.combine(date,  self.TIME_OFFSET_START) + timedelta(minutes=tatami_begin)

                    for slot in tatami["items"]:
                        if "id" in slot and slot["id"][:5] == "pause":
                            continue # skip breaks

                        slot["hash"] = hashlib.sha256(str(slot).encode()).hexdigest()

                        slot["start"] = tatami_start_time + timedelta(minutes=slot["begin"])
                        slot["end"] = slot["start"] + timedelta(minutes=slot["duration"])                        
                        slot["event"] = event_object

                        slot["tatami"] = tatami_number

                        eps.ExternalProvidedSlot.create_from_jjcm_schedule(slot)

                        hashes.append(slot["hash"])
        return hashes
    

    @classmethod
    def getSchedule(cls, eventID: int):
        print(f"Retrieving schedule for event ID: {eventID}")

        uri = f"https://jjcm.foehst.net/api/competitions/{eventID}/schedule"
        response = get(uri, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve schedule, status code: {response.status_code}, content: {response.text}")
        try:
            return response.json()
        except ValueError as e:
            raise Exception(f"Failed to parse JSON response: {e}")
