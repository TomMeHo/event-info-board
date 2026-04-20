# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Event Info Board is a Django application that displays timetables and results for Jiu Jitsu competitions. It syncs data from JJCM (jjcm.foehst.net) and displays it on info screens.

## URLs

All endpoints are prefixed with `/app/`:

- `/app/board/` - Event board showing the competition schedule (for info screens)
- `/app/schedule/` - Compact schedule view
- `/app/schedule/<id>/` - Slot detail with competitors
- `/app/registrations/` - List of registered competitors (filterable by dojo, searchable by name)
- `/app/registrations/<id>/` - Competitor detail with schedule slots
- `/app/admin/` - Django admin interface

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
docker compose down && docker compose build --no-cache && docker compose up -d  # Rebuild and restart
docker compose exec django-web python manage.py migrate        # Run migrations
docker compose exec django-web python manage.py createsuperuser # Create admin user
docker compose exec django-web python manage.py collectstatic  # Collect static files
docker compose exec django-web python manage.py loaddata rank  # Load rank fixtures
docker compose logs -f django-web                              # View logs
```

### Data Sync Commands
```bash
python manage.py getAll                             # Sync all data for active competition
python manage.py getAll <JJCM_ID>                   # Sync all data for specific competition
python manage.py getAll --force                     # Force sync even if unchanged
python manage.py getCompetitions                    # Sync all competitions from JJCM
python manage.py getCompetitions --activate <ID>    # Sync and activate specific competition
python manage.py getSchedule                        # Sync schedule for active competitions
python manage.py getSchedule <JJCM_ID>              # Sync schedule for specific competition
python manage.py getCompetitors <JJCM_ID>           # Sync competitors for competition
python manage.py getCategories <JJCM_ID>            # Sync categories per discipline (requires auth)
python manage.py getCategories --discipline kata    # Sync categories for specific discipline
python manage.py getCategories --force              # Force reload even if unchanged
python manage.py getEntries <JJCM_ID>               # Sync entries per discipline (requires auth)
python manage.py getEntries --discipline pairs      # Sync entries for specific discipline
python manage.py getEntries --force                 # Force reload even if unchanged
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
- 8. Kyu (gelb), 7. Kyu (orange), 6. Kyu (grün), 5. Kyu (blau), 4. Kyu (braun)
- 3. Kyu (braun mit 1 Streifen), 2. Kyu (braun mit 2 Streifen), 1. Kyu (braun mit 3 Streifen)

**Dan grades** (1-10):
- 1-5. Dan (schwarz with yellow stripes), 6-8. Dan (rot-weiß), 9-10. Dan (rot)

Belt visualization is rendered dynamically by `Rank.get_belt_html()`. CSS styles are in `schedule/templates/schedule/includes/belt_styles.html`.

### Data Sync Architecture
Management commands in `schedule/management/commands/` sync from JJCM API:
- Uses SHA256 hashing for change detection (schedule, entries, categories)
- Hash fields on Competition model: `jjcmHash` (schedule), `jjcmEntriesHash`, `jjcmCategoriesHash`
- Use `--force` flag to reload even if data hasn't changed
- Only one Competition can be `active=True` at a time
- API documentation and sample data in `jjcm.md` and `jjcm_samples/`

### Environment Variables
Required in `.env`:
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- `DATABASE_ENGINE`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT`
- `JJCM_BASE` (optional, defaults to https://jjcm.foehst.net)
- `JJCM_USERNAME`, `JJCM_PASSWORD` (for authenticated JJCM endpoints)

Footer configuration (optional):
- `FOOTER_LINK_URL` (defaults to https://dm2026.tv-hochstetten.de)
- `FOOTER_LINK_LABEL` (defaults to "Deutsche Meisterschaften 2026")
- `FOOTER_IMPRESSUM_URL` (defaults to https://www.tv-hochstetten.de/impressum)

### Access Gate

The `@require_access` decorator (`schedule/views.py`) protects the schedule, registrations, and slot detail views. Unauthenticated requests are redirected to `/app/access/`.

Access is granted via one of two mechanisms, both stored in the Django session (`access_granted = True`):

**Password:** Set `ACCESS_PASSWORD` in `.env`. Users enter it at `/app/access/`.

**QR token:** Set `ACCESS_TOKEN` in `.env`. Append `?t=<token>` to any protected URL — the token is validated, the session is marked as granted, and the user is redirected to the clean URL (token stripped). This is the intended mechanism for QR codes: generate a QR code pointing to e.g. `https://your-host/app/schedule/?t=<ACCESS_TOKEN>` and scan it to gain access without typing a password.

Both variables are optional. If `ACCESS_TOKEN` is empty, token-based access is disabled. If `ACCESS_PASSWORD` is empty, password-based access is disabled.

### OIDC Authentication (PocketID)
Optional OIDC/PocketID authentication. Set `DJANGO_OIDC_ENABLED=True` to enable.

Required environment variables when enabled:
```
DJANGO_OIDC_ENABLED=True
DJANGO_OIDC_CLIENT_ID=your-client-id
DJANGO_OIDC_CLIENT_SECRET=your-client-secret
DJANGO_OIDC_AUTHORIZATION_ENDPOINT=https://your-pocketid.example.com/authorize
DJANGO_OIDC_TOKEN_ENDPOINT=https://your-pocketid.example.com/token
DJANGO_OIDC_USER_ENDPOINT=https://your-pocketid.example.com/userinfo
DJANGO_OIDC_JWKS_ENDPOINT=https://your-pocketid.example.com/.well-known/jwks.json
DJANGO_OIDC_SIGN_ALGO=RS256
```

OIDC endpoints when enabled:
- `/app/oidc/authenticate/` - Start OIDC login
- `/app/oidc/callback/` - OIDC callback (redirect URI to configure in PocketID)
- `/app/oidc/logout/` - OIDC logout

Admin login integration:
- When OIDC is enabled, the Django admin login page (`/app/admin/`) shows a "Login with PocketID" button
- Users can still use local Django credentials or OIDC
- OIDC users are automatically created in Django on first login
