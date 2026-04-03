from django.core.management.base import BaseCommand, CommandError, CommandParser
import hashlib
import os
import requests
from schedule.models import Competition, Category, Entry


class Command(BaseCommand):
    help = 'Retrieves categories per discipline from the JJ competition manager.'

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
            help="JJCM ID of the competition to retrieve categories for."
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
            help="Only show categories, don't save to database"
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
            # Try to get active competition
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

        disciplines = [options['discipline']] if options.get('discipline') else self.DISCIPLINES

        # Fetch all data first to compute hash
        all_categories_data = {}
        for discipline in disciplines:
            all_categories_data[discipline] = self.fetch_categories(session, competition_id, discipline)

        # Compute hash of all categories data
        categories_hash = hashlib.sha256(str(all_categories_data).encode()).hexdigest()

        if not force and competition.jjcmCategoriesHash == categories_hash:
            self.stdout.write(self.style.SUCCESS(f"Categories for '{competition}' have not changed, skipping."))
            return

        self.stdout.write(f"Categories for '{competition}' have changed, updating...")

        total_created = 0
        total_updated = 0

        for discipline in disciplines:
            categories_data = all_categories_data[discipline]
            self.stdout.write(f"\n{discipline}: {len(categories_data)} categories")

            if dry_run:
                for cat in categories_data:
                    cat_info = cat.get('category', {})
                    self.stdout.write(f"  - {cat.get('name')} (id={cat_info.get('id')}, entries={cat.get('cardinality', 0)})")
            else:
                created, updated = self.save_categories(categories_data, competition, discipline)
                total_created += created
                total_updated += updated

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDry run - no changes saved"))
        else:
            # Save hash
            competition.jjcmCategoriesHash = categories_hash
            competition.save(update_fields=['jjcmCategoriesHash'])
            self.stdout.write(self.style.SUCCESS(
                f"\nSaved {total_created} new, updated {total_updated} existing categories"
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
        """Select a competition in the JJCM session (required before fetching categories)."""
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

    def fetch_categories(self, session, competition_id: int, discipline: str) -> list:
        """Fetch categories for a specific discipline."""
        base = os.getenv('JJCM_BASE', 'https://jjcm.foehst.net')
        url = f"{base}/api/competitions/{competition_id}/{discipline}/categories"

        try:
            resp = session.get(url, timeout=10)
        except requests.RequestException as e:
            self.stderr.write(f"Failed to fetch {discipline} categories: {e}")
            return []

        if resp.status_code != 200:
            self.stderr.write(f"Failed to fetch {discipline} categories: {resp.status_code}")
            return []

        try:
            return resp.json()
        except ValueError as e:
            self.stderr.write(f"Failed to parse {discipline} categories JSON: {e}")
            return []

    def save_categories(self, categories_data: list, competition: Competition, discipline: str) -> tuple:
        """Save categories to the database and link entries to categories.

        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        saved_ids = []

        for cat_data in categories_data:
            category, created = Category.create_from_jjcm(cat_data, competition, discipline)
            if category.jjcmCategoryId:
                saved_ids.append(category.jjcmCategoryId)

            if created:
                created_count += 1
                self.stdout.write(f"  + {category.name}")
            else:
                updated_count += 1
                self.stdout.write(f"  ~ {category.name}")

            # Link entries to this category
            entries_data = cat_data.get('entries', [])
            if entries_data:
                entry_ids = [e.get('id') for e in entries_data if e.get('id')]
                linked = Entry.objects.filter(jjcmEntryId__in=entry_ids).update(category=category)
                if linked:
                    self.stdout.write(f"    -> Linked {linked} entries")

        # Map discipline key to model choice for cleanup
        discipline_map = {
            'random_attack': Category.Discipline.RANDOM_ATTACK,
            'ground_fighting': Category.Discipline.GROUND_FIGHTING,
            'ground_fighting_open': Category.Discipline.GROUND_FIGHTING_OPEN,
            'pairs': Category.Discipline.PAIRS,
            'kata': Category.Discipline.KATA,
            'team': Category.Discipline.TEAM,
        }
        model_discipline = discipline_map.get(discipline, discipline)

        # Clean up stale categories (those with IDs not in the current response)
        deleted_count, _ = Category.objects.filter(
            competition=competition,
            discipline=model_discipline,
            jjcmCategoryId__isnull=False
        ).exclude(
            jjcmCategoryId__in=saved_ids
        ).delete()

        if deleted_count:
            self.stdout.write(f"  - Removed {deleted_count} stale categories")

        return created_count, updated_count
