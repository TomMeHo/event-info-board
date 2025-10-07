# event-info-board

Timetable and result displays for a Jiu Jitsu competition.

The tool is able to collect events from the DJJB competition software and to show it on a board that can be used on info screens.

## Commands

- `python manage.py getSchedule` collects the schedule and updates time slots.

# Installation

    1. download the repo.
    1. adjust .env
    1. `docker compose up`
    1. `docker compose run django-web python manage.py migrate`
    1. `docker compose run django-web python manage.py createsuperuser`
    1. `docker compose run django-web python manage.py check --deploy`
    1. `docker compose run django-web python python manage.py collectstatic`

The image is also available on dockerhub: [tomho/jj-event-info-board](https://hub.docker.com/repository/docker/tomho/jj-event-info-board/general)