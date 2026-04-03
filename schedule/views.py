from django.http import HttpResponse
from django.template import loader
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.db.models import Q

import json
from datetime import datetime

from .models import Competition, Slot, ExternalProvidedSlot, Registration, Dojo


def event_board(request):
    competitions = Competition.objects.filter(active=True).order_by("firstDay")
    competition = competitions[0] if (len(competitions) > 0) else None

    if (competition is None):
        context = { 'event': 'Kein Wettkampf ausgewählt.', 'day': None, 'days': [{ 'slots': [] }] }
        return HttpResponse( loader.get_template("schedule/event_board.html").render(context, request))

    #TODO add second day

    non_competition_slots = Slot.objects.filter(competition=competition).filter(start__date=competition.firstDay).exclude(polymorphic_ctype=ContentType.objects.get_for_model(ExternalProvidedSlot)).all()
    competition_slots = ExternalProvidedSlot.objects.filter(competition=competition).filter(start__date=competition.firstDay).order_by("start").order_by("tatami").all()

    last_group = ""
    combined_slots = []
    group_node = None

    for slot in competition_slots:
        slot.started = True if (slot.start > datetime.now()) else False
        slot.ended = True if (slot.end < datetime.now()) else False

        slot.title = slot.category_name
        slot.round_type = slot.type

        if last_group != f"{slot.discipline} {slot.tatami}":
            last_group = f"{slot.discipline} {slot.tatami}"
            group_node = None

        if group_node is None:
            group_node = { 'type': 'group', 'title': slot.discipline, 'start': slot.start, 'tatami': slot.tatami, 'slots': [] }
            combined_slots.append(group_node)

        slot.type = 'subitem'
        group_node["slots"].append(slot)

    for slot in non_competition_slots:
        slot.type = 'item'
        combined_slots.append(slot)

    def extract_start(slot):
        try:
            return slot['start'] # the json way...
        except:
            return slot.start # the django model way...

    combined_slots.sort( key=extract_start )


    context = { 'event': competition, 'day': competition.firstDay, 'days': [{ 'slots': combined_slots }] }

    return HttpResponse( loader.get_template("schedule/event_board.html").render(context, request))


def registrations_list(request):
    """List all registrations for the active competition with filter and search."""
    competitions = Competition.objects.filter(active=True).order_by("firstDay")
    competition = competitions.first()

    if competition is None:
        context = {'event': None, 'registrations': [], 'dojos': [], 'search': '', 'dojo_filter': ''}
        return HttpResponse(loader.get_template("schedule/registrations_list.html").render(context, request))

    # Get filter parameters
    search = request.GET.get('search', '').strip()
    dojo_filter = request.GET.get('dojo', '')

    # Base queryset
    registrations = Registration.objects.filter(competition=competition).select_related('competitor', 'dojo').order_by('competitor__name', 'competitor__givenName')

    # Apply dojo filter
    if dojo_filter:
        registrations = registrations.filter(dojo_id=dojo_filter)

    # Apply name search
    if search:
        registrations = registrations.filter(
            Q(competitor__name__icontains=search) | Q(competitor__givenName__icontains=search)
        )

    # Get all dojos for the filter dropdown
    dojos = Dojo.objects.filter(registrations__competition=competition).distinct().order_by('name')

    context = {
        'event': competition,
        'registrations': registrations,
        'dojos': dojos,
        'search': search,
        'dojo_filter': dojo_filter,
    }

    return HttpResponse(loader.get_template("schedule/registrations_list.html").render(context, request))


def registration_detail(request, registration_id):
    """Show detail view for a registration including schedule slots."""
    registration = get_object_or_404(
        Registration.objects.select_related('competitor', 'dojo', 'competition'),
        pk=registration_id
    )

    # Get schedule slots for this registration
    slots = registration.slots.all().order_by('start')

    context = {
        'event': registration.competition,
        'registration': registration,
        'competitor': registration.competitor,
        'slots': slots,
    }

    return HttpResponse(loader.get_template("schedule/registration_detail.html").render(context, request))


def schedule_compact(request):
    """Compact schedule view for the active competition."""
    competitions = Competition.objects.filter(active=True).order_by("firstDay")
    competition = competitions.first()

    if competition is None:
        context = {'event': None, 'days': []}
        return HttpResponse(loader.get_template("schedule/schedule_compact.html").render(context, request))

    # Get all slots for the competition, grouped by day
    slots = ExternalProvidedSlot.objects.filter(competition=competition).order_by('start', 'tatami')

    # Group by date
    days = {}
    for slot in slots:
        day_key = slot.start.date()
        if day_key not in days:
            days[day_key] = []
        days[day_key].append(slot)

    # Convert to list of dicts sorted by date
    days_list = [{'date': date, 'slots': slots} for date, slots in sorted(days.items())]

    context = {
        'event': competition,
        'days': days_list,
    }

    return HttpResponse(loader.get_template("schedule/schedule_compact.html").render(context, request))


def slot_detail(request, slot_id):
    """Detail view for a schedule slot including competitors."""
    slot = get_object_or_404(
        ExternalProvidedSlot.objects.select_related('competition'),
        pk=slot_id
    )

    # Get registrations for this slot
    registrations = slot.registrations.select_related('competitor', 'dojo').order_by('competitor__name', 'competitor__givenName')

    context = {
        'event': slot.competition,
        'slot': slot,
        'registrations': registrations,
    }

    return HttpResponse(loader.get_template("schedule/slot_detail.html").render(context, request))