from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Synchronizes all data from JJCM: competitions, schedule, competitors, entries, and categories.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "competition_id",
            type=int,
            nargs='?',
            help="JJCM ID of the competition to sync. If not provided, syncs active competition."
        )
        parser.add_argument(
            "--force",
            action='store_true',
            help="Force reload even if data hasn't changed"
        )

    def handle(self, *args, **options):
        competition_id = options.get('competition_id')
        force = options.get('force', False)

        force_args = ['--force'] if force else []

        # 1. Sync competitions
        self.stdout.write(self.style.HTTP_INFO("\n=== Syncing Competitions ==="))
        try:
            if competition_id:
                call_command('getCompetitions', '--activate', str(competition_id), stdout=self.stdout)
            else:
                call_command('getCompetitions', stdout=self.stdout)
        except Exception as e:
            self.stderr.write(f"Error syncing competitions: {e}")

        # 2. Sync competitors/registrations (before schedule, so registrations can be linked to slots)
        self.stdout.write(self.style.HTTP_INFO("\n=== Syncing Competitors ==="))
        try:
            if competition_id:
                call_command('getCompetitors', competition_id, stdout=self.stdout)
            else:
                call_command('getCompetitors', stdout=self.stdout)
        except Exception as e:
            self.stderr.write(f"Error syncing competitors: {e}")

        # 3. Sync schedule (after competitors, so slots can link to registrations)
        self.stdout.write(self.style.HTTP_INFO("\n=== Syncing Schedule ==="))
        try:
            if competition_id:
                call_command('getSchedule', competition_id, stdout=self.stdout)
            else:
                call_command('getSchedule', stdout=self.stdout)
        except Exception as e:
            self.stderr.write(f"Error syncing schedule: {e}")

        # 4. Sync entries (requires auth)
        self.stdout.write(self.style.HTTP_INFO("\n=== Syncing Entries ==="))
        try:
            if competition_id:
                call_command('getEntries', competition_id, *force_args, stdout=self.stdout)
            else:
                call_command('getEntries', *force_args, stdout=self.stdout)
        except Exception as e:
            self.stderr.write(f"Error syncing entries: {e}")

        # 5. Sync categories (requires auth, links entries)
        self.stdout.write(self.style.HTTP_INFO("\n=== Syncing Categories ==="))
        try:
            if competition_id:
                call_command('getCategories', competition_id, *force_args, stdout=self.stdout)
            else:
                call_command('getCategories', *force_args, stdout=self.stdout)
        except Exception as e:
            self.stderr.write(f"Error syncing categories: {e}")

        self.stdout.write(self.style.SUCCESS("\n=== Sync Complete ==="))
