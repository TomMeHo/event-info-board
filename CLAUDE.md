# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Event Info Board is a Django application that displays timetables and results for Jiu Jitsu competitions. It syncs data from JJCM (jjcm.foehst.net) and displays it on info screens.

## URLs

- `/board/` - Event board showing the competition schedule (for info screens)
- `/schedule/` - Compact schedule view
- `/schedule/<id>/` - Slot detail with competitors
- `/registrations/` - List of registered competitors (filterable by dojo, searchable by name)
- `/registrations/<id>/` - Competitor detail with schedule slots
- `/admin/` - Django admin interface

## Development Commands

### Local Development (with devcontainer or pipenv)
```bash
pipenv sync --system --dev          # Install dependencies
python manage.py runserver          # Start dev server
python manage.py test               # Run tests
python manage.py makemigrations     # Create migrations
python manage.py migrate            # Apply migrations
```

### Docker Development
```bash
docker compose up                                              # Start services
docker compose run django-web python manage.py migrate         # Run migrations
docker compose run django-web python manage.py createsuperuser # Create admin user
docker compose run django-web python manage.py collectstatic   # Collect static files
```

### Data Sync Commands
```bash
python manage.py getCompetitions                    # Sync all competitions from JJCM
python manage.py getCompetitions --activate <ID>    # Sync and activate specific competition
python manage.py getSchedule                        # Sync schedule for active competitions
python manage.py getSchedule <JJCM_ID>              # Sync schedule for specific competition
python manage.py getCompetitors <JJCM_ID>           # Sync competitors for competition
python manage.py loaddata rank                      # Load rank fixtures (DJJB graduation system)
```

### Test Coverage
```bash
coverage run --source='.' --branch manage.py test schedule
coverage report --omit=manage.py,*/migrations/*
```

## Architecture

### Django Apps
- **eventBoard/**: Main Django project (settings, urls, wsgi)
- **schedule/**: Core app with models, views, and management commands

### Model Hierarchy
The `schedule` app uses django-polymorphic for slot types:

```
Competition (jjcmCompetitionId, title, active)
    │
    ├── Registration (links Competitor to Competition with dojo, ranks)
    │       └── Competitor (person: name, givenName, sex)
    │       └── Dojo (jjcmDojoId, name)
    │
    └── Slot (polymorphic base: start, end, title)
            └── ExternalProvidedSlot (JJCM slots: discipline, category_name, tatami, hash)
                    └── registrations (M:N to Registration)
```

### Key Model Files
- `schedule/models/competition.py` - Uses `db_table='schedule_event'` for legacy compatibility
- `schedule/models/externalProvidedSlot.py` - Schedule slots from JJCM with hash-based change detection
- `schedule/models/registration.py` - Competition-specific data linking Competitor to Competition, includes `rank` property to fetch Rank object
- `schedule/models/ranks.py` - Rank model with belt visualization methods (`get_belt_html()`, `get_display_html()`)

### Rank System (DJJB)
Ranks are stored in `schedule/fixtures/rank.json` and loaded via `python manage.py loaddata rank`.

**Mon grades** (children, 1-8):
- 1. Mon (weiß-blau), 2. Mon (blau), 3. Mon (weiß-grün), 4. Mon (grün)
- 5. Mon (weiß-orange), 6. Mon (orange), 7. Mon (weiß-gelb), 8. Mon (gelb)

**Kyu grades** (8-1):
- 8. Kyu (gelb), 7. Kyu (orange), 6. Kyu (grün), 5. Kyu (blau), 4. Kyu (blau)
- 3. Kyu (braun), 2. Kyu (braun mit 1 Streifen), 1. Kyu (braun mit 2 Streifen)

**Dan grades** (1-10):
- 1-5. Dan (schwarz with yellow stripes), 6-8. Dan (rot-weiß), 9-10. Dan (rot)

Belt visualization is rendered dynamically by `Rank.get_belt_html()`. CSS styles are in `schedule/templates/schedule/includes/belt_styles.html`.

### Data Sync Architecture
Management commands in `schedule/management/commands/` sync from JJCM API:
- Uses SHA256 hashing for change detection (computed in model's `save()` method)
- Only one Competition can be `active=True` at a time
- API documentation and sample data in `jjcm.md` and `jjcm_samples/`

### Environment Variables
Required in `.env`:
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- `DATABASE_ENGINE`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT`
- `JJCM_BASE` (optional, defaults to https://jjcm.foehst.net)
- `JJCM_USERNAME`, `JJCM_PASSWORD` (for authenticated JJCM endpoints)
