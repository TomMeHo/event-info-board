# event-info-board

Timetable and result displays for a Jiu Jitsu competition.

The tool is able to collect events from the DJJB competition software and to show it on a board that can be used on info screens.

## URLs

All endpoints are prefixed with `/app/`:

- `/app/board/` - Event board showing the competition schedule (for info screens)
- `/app/schedule/` - Compact schedule view
- `/app/schedule/<id>/` - Slot detail with competitors
- `/app/registrations/` - List of registered competitors (filterable by dojo, searchable by name)
- `/app/registrations/<id>/` - Competitor detail with schedule slots
- `/app/admin/` - Django admin interface

## Commands

- `python manage.py getAll` syncs all data for active competition (use `--force` to reload even if unchanged)
- `python manage.py getCompetitions` syncs competitions from JJCM (use `--activate <ID>` to activate one)
- `python manage.py getSchedule` collects the schedule and updates time slots (use `--force` to reload)
- `python manage.py getCompetitors <ID>` collects the competitors for a competition
- `python manage.py getEntries <ID>` syncs entries per discipline (requires auth)
- `python manage.py getCategories <ID>` syncs categories per discipline (requires auth)

## Environment Variables

### Django Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | (required) |
| `DJANGO_DEBUG` | Enable debug mode | `False` |
| `DJANGO_LOGLEVEL` | Logging level | `INFO` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | CSRF trusted origins | |

### Database
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_ENGINE` | Database engine | `postgresql` |
| `DATABASE_NAME` | Database name | |
| `DATABASE_USERNAME` | Database user | |
| `DATABASE_PASSWORD` | Database password | |
| `DATABASE_HOST` | Database host | `db` |
| `DATABASE_PORT` | Database port | `5432` |

### JJCM API
| Variable | Description | Default |
|----------|-------------|---------|
| `JJCM_BASE` | JJCM API base URL | `https://jjcm.foehst.net` |
| `JJCM_USERNAME` | JJCM login email | |
| `JJCM_PASSWORD` | JJCM login password | |

### OIDC Authentication (optional)
| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_OIDC_ENABLED` | Enable OIDC authentication | `False` |
| `DJANGO_OIDC_CLIENT_ID` | OIDC client ID | |
| `DJANGO_OIDC_CLIENT_SECRET` | OIDC client secret | |
| `DJANGO_OIDC_AUTHORIZATION_ENDPOINT` | OIDC authorization endpoint | |
| `DJANGO_OIDC_TOKEN_ENDPOINT` | OIDC token endpoint | |
| `DJANGO_OIDC_USER_ENDPOINT` | OIDC userinfo endpoint | |
| `DJANGO_OIDC_JWKS_ENDPOINT` | OIDC JWKS endpoint | |
| `DJANGO_OIDC_SIGN_ALGO` | OIDC signing algorithm | `RS256` |

### Footer
| Variable | Description | Default |
|----------|-------------|---------|
| `FOOTER_LINK_URL` | Footer link URL | `https://dm2026.tv-hochstetten.de` |
| `FOOTER_LINK_LABEL` | Footer link label | `Deutsche Meisterschaften 2026` |
| `FOOTER_IMPRESSUM_URL` | Impressum link URL | `https://www.tv-hochstetten.de/impressum` |

## Installation

1. Download the repo
2. Copy `.env.example` to `.env` and adjust values
3. `docker compose up`
4. `docker compose exec django-web python manage.py migrate`
5. `docker compose exec django-web python manage.py createsuperuser`
6. `docker compose exec django-web python manage.py collectstatic`
7. `docker compose exec django-web python manage.py loaddata rank`

The image is also available on dockerhub: [tomho/jj-event-info-board](https://hub.docker.com/repository/docker/tomho/jj-event-info-board/general)