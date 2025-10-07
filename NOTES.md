# event-info-board

Timetable and result displays for a competition


# Pipenv

https://pipenv.pypa.io/en/latest/installation.html#make-sure-you-have-python-and-pip
We're using pipenv. This means, adding packages with ``pipenv install --system <package> ``

`` pipenv lock `` generates the lock file and the pipfile.
`` pipenv sync --system --dev`` syncs with the pipfile. ``--system`` makes pipenv install this to the system, not the environment.

`` pipenv install pytest --dev`` installs dev-related packages, such as for testing.

# Testing

## Measuring coverage

To measure coverage, run:

``coverage run --source='.' --branch manage.py test time_recording`` (with timesheet set to app name).
``coverage report --omit=manage.py,*/migrations/*,`` prints the result.
``coverage html --omit=manage.py,*/migrations/*,`` prints the result.

# Implementation aspects

## Time Accounting Fields

Requires Polymorphism. A very good article is https://realpython.com/modeling-polymorphism-django-python/.

## Deployment

- [Preparing deployment](https://medium.com/@anzaloquin/deploying-django-and-hugo-on-hetzner-a-complete-guide-f90f860aed42)
- [Deployment in Container](https://www.docker.com/blog/how-to-dockerize-django-app/)
- [Static files in django](https://joshua-etim.medium.com/serving-static-files-with-django-it-100-works-70f436e59587)

To activate this project's virtualenv, run pipenv shell.
Alternatively, run a command inside the virtualenv with pipenv run.