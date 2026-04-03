from django.core.management.base import BaseCommand, CommandError, CommandParser
import hashlib
import os
import requests
from schedule.models import (
    Competition, Dojo, Entry, SingleCompetitorEntry, PairsEntry, KataEntry, TeamEntry
)


class Command(BaseCommand):
    help = 'Retrieves entries (discipline registrations) from the JJ competition manager.'

    DISCIPLINES = [
        'random_attack',
        'ground_fighting',
        'ground_fighting_open',
        'pairs',
        'kata',
        'team',
    ]

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "competition_id",
            type=int,
            nargs='?',
            help="JJCM ID of the competition to retrieve entries for."
        )
        parser.add_argument(
            "--discipline",
            type=str,
            choices=self.DISCIPLINES,
            help="Specific discipline to fetch (default: all)"
        )
        parser.add_argument(
            "--dry-run",
            action='store_true',
            help="Only show entries, don't save to database"
        )
        parser.add_argument(
            "--force",
            action='store_true',
            help="Force reload even if data hasn't changed"
        )

    def handle(self, *args, **options):
        competition_id = options.get('competition_id')
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)

        if not competition_id:
            competition = Competition.objects.filter(active=True).first()
            if not competition or not competition.jjcmCompetitionId:
                raise CommandError('Please provide a competition_id or set an active competition with jjcmCompetitionId')
            competition_id = competition.jjcmCompetitionId
        else:
            competition = Competition.objects.filter(jjcmCompetitionId=competition_id).first()
            if not competition:
                raise CommandError(f'No Competition found with jjcmCompetitionId={competition_id}')

        session = self.login()
        self.select_competition(session, competition_id)

        # Cache dojos
        self.dojo_cache = {d.jjcmDojoId: d for d in Dojo.objects.all()}

        disciplines = [options['discipline']] if options.get('discipline') else self.DISCIPLINES

        # Fetch all data first to compute hash
        all_entries_data = {}
        for discipline in disciplines:
            rel_param = '?rel=members' if discipline == 'team' else ''
            all_entries_data[discipline] = self.fetch_entries(session, competition_id, discipline, rel_param)

        # Compute hash of all entries data
        entries_hash = hashlib.sha256(str(all_entries_data).encode()).hexdigest()

        if not force and competition.jjcmEntriesHash == entries_hash:
            self.stdout.write(self.style.SUCCESS(f"Entries for '{competition}' have not changed, skipping."))
            return

        self.stdout.write(f"Entries for '{competition}' have changed, updating...")

        total_created = 0
        total_updated = 0

        for discipline in disciplines:
            entries_data = all_entries_data[discipline]
            self.stdout.write(f"\n{discipline}: {len(entries_data)} entries")

            if dry_run:
                for entry in entries_data:
                    self.stdout.write(f"  - id={entry.get('id')} type={entry.get('type')}")
            else:
                created, updated = self.save_entries(entries_data, competition, discipline)
                total_created += created
                total_updated += updated

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDry run - no changes saved"))
        else:
            # Save hash
            competition.jjcmEntriesHash = entries_hash
            competition.save(update_fields=['jjcmEntriesHash'])
            self.stdout.write(self.style.SUCCESS(
                f"\nSaved {total_created} new, updated {total_updated} existing entries"
            ))

    def login(self):
        """Log in to the JJCM API and return an authenticated session."""
        base = os.getenv('JJCM_BASE', 'https://jjcm.foehst.net')
        login_url = f"{base}/api/auth"

        username = os.getenv('JJCM_USERNAME')
        password = os.getenv('JJCM_PASSWORD')
        if not username or not password:
            raise CommandError('Please set JJCM_USERNAME and JJCM_PASSWORD environment variables')

        session = requests.Session()

        self.stdout.write("Logging in to JJCM API...")
        try:
            resp = session.post(login_url, json={'username': username, 'password': password}, timeout=10)
        except requests.RequestException as e:
            raise CommandError(f"Login request failed: {e}")

        if resp.status_code not in (200, 201, 204):
            raise CommandError(f"Login failed: {resp.status_code} - {resp.text}")

        self.stdout.write(self.style.SUCCESS(f"Login successful (status {resp.status_code})"))
        return session

    def select_competition(self, session, competition_id: int):
        """Select a competition in the JJCM session."""
        base = os.getenv('JJCM_BASE', 'https://jjcm.foehst.net')
        select_url = f"{base}/api/competitions/{competition_id}/select"

        self.stdout.write(f"Selecting competition {competition_id}...")
        try:
            resp = session.get(select_url, timeout=10)
        except requests.RequestException as e:
            raise CommandError(f"Failed to select competition: {e}")

        if resp.status_code != 200:
            raise CommandError(f"Failed to select competition: {resp.status_code} - {resp.text}")

        self.stdout.write(self.style.SUCCESS(f"Competition {competition_id} selected"))

    def fetch_entries(self, session, competition_id: int, discipline: str, rel_param: str = '') -> list:
        """Fetch entries for a specific discipline."""
        base = os.getenv('JJCM_BASE', 'https://jjcm.foehst.net')
        url = f"{base}/api/competitions/{competition_id}/{discipline}/entries{rel_param}"

        try:
            resp = session.get(url, timeout=10)
        except requests.RequestException as e:
            self.stderr.write(f"Failed to fetch {discipline} entries: {e}")
            return []

        if resp.status_code != 200:
            self.stderr.write(f"Failed to fetch {discipline} entries: {resp.status_code}")
            return []

        try:
            return resp.json()
        except ValueError as e:
            self.stderr.write(f"Failed to parse {discipline} entries JSON: {e}")
            return []

    def get_dojo(self, dojo_id: int) -> Dojo:
        """Get Dojo from cache."""
        return self.dojo_cache.get(dojo_id) if dojo_id else None

    def save_entries(self, entries_data: list, competition: Competition, discipline: str) -> tuple:
        """Save entries to the database."""
        created_count = 0
        updated_count = 0
        saved_ids = []

        for entry_data in entries_data:
            dojo = self.get_dojo(entry_data.get('dojo_id'))
            entry_id = entry_data.get('id')
            saved_ids.append(entry_id)

            try:
                if discipline in ('random_attack', 'ground_fighting', 'ground_fighting_open'):
                    entry, created = SingleCompetitorEntry.create_from_jjcm(
                        entry_data, competition, discipline, dojo
                    )
                elif discipline == 'pairs':
                    entry, created = PairsEntry.create_from_jjcm(entry_data, competition, dojo)
                elif discipline == 'kata':
                    entry, created = KataEntry.create_from_jjcm(entry_data, competition, dojo)
                elif discipline == 'team':
                    entry, created = TeamEntry.create_from_jjcm(
                        entry_data, competition, dojo, entry_data.get('members', [])
                    )
                else:
                    self.stderr.write(f"Unknown discipline: {discipline}")
                    continue

                if created:
                    created_count += 1
                    self.stdout.write(f"  + {entry}")
                else:
                    updated_count += 1
                    self.stdout.write(f"  ~ {entry}")

            except Exception as e:
                self.stderr.write(f"  ! Error saving entry {entry_id}: {e}")

        # Clean up stale entries for this discipline
        deleted_count = 0
        if discipline in ('random_attack', 'ground_fighting', 'ground_fighting_open'):
            discipline_map = {
                'random_attack': SingleCompetitorEntry.Discipline.RANDOM_ATTACK,
                'ground_fighting': SingleCompetitorEntry.Discipline.GROUND_FIGHTING,
                'ground_fighting_open': SingleCompetitorEntry.Discipline.GROUND_FIGHTING_OPEN,
            }
            deleted_count, _ = SingleCompetitorEntry.objects.filter(
                competition=competition,
                discipline=discipline_map[discipline]
            ).exclude(jjcmEntryId__in=saved_ids).delete()
        elif discipline == 'pairs':
            deleted_count, _ = PairsEntry.objects.filter(
                competition=competition
            ).exclude(jjcmEntryId__in=saved_ids).delete()
        elif discipline == 'kata':
            deleted_count, _ = KataEntry.objects.filter(
                competition=competition
            ).exclude(jjcmEntryId__in=saved_ids).delete()
        elif discipline == 'team':
            deleted_count, _ = TeamEntry.objects.filter(
                competition=competition
            ).exclude(jjcmEntryId__in=saved_ids).delete()

        if deleted_count:
            self.stdout.write(f"  - Removed {deleted_count} stale entries")

        return created_count, updated_count
