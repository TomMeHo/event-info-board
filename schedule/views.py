from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
from django.urls import reverse
from functools import wraps

import json
from collections import defaultdict
from datetime import datetime

from .models import (
    Competition, Slot, ExternalProvidedSlot, Registration, Dojo,
    Entry, SingleCompetitorEntry, PairsEntry, KataEntry, TeamEntry, TickerMessage
)


def require_access(view_func):
    """Require shared-password or QR-token access for a view."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.session.get('access_granted'):
            return view_func(request, *args, **kwargs)
        token = request.GET.get('t', '')
        if token and settings.ACCESS_TOKEN and token == settings.ACCESS_TOKEN:
            request.session['access_granted'] = True
            request.session.set_expiry(172800)  # 48 hours
            # Redirect to clean URL without the token parameter
            params = request.GET.copy()
            params.pop('t')
            clean_url = request.path
            if params:
                clean_url += '?' + params.urlencode()
            return redirect(clean_url)
        return redirect(reverse('access_gate') + '?next=' + request.path)
    return wrapper


def access_gate(request):
    """Password / token entry page for gated content."""
    next_url = request.GET.get('next', reverse('schedule_compact'))
    error = None

    # Token in query string on this page (fallback)
    token = request.GET.get('t', '')
    if token and settings.ACCESS_TOKEN and token == settings.ACCESS_TOKEN:
        request.session['access_granted'] = True
        request.session.set_expiry(172800)  # 48 hours
        return redirect(next_url)

    if request.method == 'POST':
        next_url = request.POST.get('next', next_url)
        password = request.POST.get('password', '')
        if settings.ACCESS_PASSWORD and password == settings.ACCESS_PASSWORD:
            request.session['access_granted'] = True
            request.session.set_expiry(172800)  # 48 hours
            return redirect(next_url)
        error = 'Falsches Passwort. Bitte erneut versuchen.'

    context = {'next': next_url, 'error': error}
    return HttpResponse(loader.get_template('schedule/access_gate.html').render(context, request))


def event_board(request):
    competitions = Competition.objects.filter(active=True).order_by("firstDay")
    competition = competitions[0] if (len(competitions) > 0) else None

    if competition is None:
        context = {
            'event': 'Kein Wettkampf ausgewählt.',
            'day': None,
            'main_slots': [],
            'detail_slots': [],
            'ticker_segments': [],
            'board_main_seconds': settings.BOARD_MAIN_SECONDS,
            'board_detail_seconds': settings.BOARD_DETAIL_SECONDS,
        }
        return HttpResponse(loader.get_template("schedule/event_board.html").render(context, request))

    now = datetime.now()
    today = competition.firstDay

    # --- Main view: non-past manual slots only ---
    manual_slots = (
        Slot.objects.filter(competition=competition)
        .exclude(polymorphic_ctype=ContentType.objects.get_for_model(ExternalProvidedSlot))
        .filter(end__gte=now)
        .order_by("start")
    )
    main_slots = []
    for slot in manual_slots:
        slot.type = 'item'
        main_slots.append(slot)

    # --- Detail view: top-2 per tatami + flagged manual slots ---
    competition_slots = (
        ExternalProvidedSlot.objects.filter(competition=competition)
        .filter(start__date=today)
        .filter(end__gte=now)
        .order_by("tatami", "start")
    )

    # Group by tatami, pick current-or-next as slot 1, next as slot 2
    tatami_slots = defaultdict(list)
    for slot in competition_slots:
        tatami_slots[slot.tatami].append(slot)

    detail_slots = []
    for tatami, slots in sorted(tatami_slots.items()):
        # slot 1: currently active (start <= now <= end), else first upcoming
        active = [s for s in slots if s.start <= now]
        upcoming = [s for s in slots if s.start > now]
        if active:
            top2 = [active[-1]]  # most recently started
            if upcoming:
                top2.append(upcoming[0])
        else:
            top2 = upcoming[:2]

        if not top2:
            continue

        for s in top2:
            s.title = s.category_name
            s.round_type = s.type
            s.type = 'subitem'

        group = {
            'type': 'group',
            'title': top2[0].discipline,
            'start': top2[0].start,
            'tatami': tatami,
            'slots': top2,
        }
        detail_slots.append(group)

    # Add manual slots flagged for detail view
    detail_manual = (
        Slot.objects.filter(competition=competition)
        .exclude(polymorphic_ctype=ContentType.objects.get_for_model(ExternalProvidedSlot))
        .filter(show_on_detail=True)
        .filter(end__gte=now)
        .order_by("start")
    )
    for slot in detail_manual:
        slot.type = 'item'
        detail_slots.append(slot)

    def extract_start(slot):
        try:
            start = slot['start']
            is_external = 1
        except TypeError:
            start = slot.start
            is_external = 0
        return (start, is_external)

    detail_slots.sort(key=extract_start)

    # --- Ticker messages ---
    ticker_qs = TickerMessage.objects.filter(competition=competition).filter(
        Q(start__isnull=True) | Q(start__lte=now)
    ).filter(
        Q(end__isnull=True) | Q(end__gte=now)
    ).order_by('order')
    ticker_segments = [{'text': t.text, 'highlighted': t.highlighted} for t in ticker_qs]

    context = {
        'event': competition,
        'day': today,
        'main_slots': main_slots,
        'detail_slots': detail_slots,
        'ticker_segments': ticker_segments,
        'board_main_seconds': settings.BOARD_MAIN_SECONDS,
        'board_detail_seconds': settings.BOARD_DETAIL_SECONDS,
    }
    return HttpResponse(loader.get_template("schedule/event_board.html").render(context, request))


@require_access
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


@require_access
def registration_detail(request, registration_id):
    """Show detail view for a registration including schedule slots and entries."""
    registration = get_object_or_404(
        Registration.objects.select_related('competitor', 'dojo', 'competition'),
        pk=registration_id
    )

    # Get schedule slots for this registration
    slots = registration.slots.all().order_by('start')

    # Get entries by type
    random_attack_entries = SingleCompetitorEntry.objects.filter(
        competitor=registration,
        discipline=SingleCompetitorEntry.Discipline.RANDOM_ATTACK
    ).select_related('category')

    ground_fighting_entries = SingleCompetitorEntry.objects.filter(
        competitor=registration,
        discipline=SingleCompetitorEntry.Discipline.GROUND_FIGHTING
    ).select_related('category')

    ground_fighting_open_entries = SingleCompetitorEntry.objects.filter(
        competitor=registration,
        discipline=SingleCompetitorEntry.Discipline.GROUND_FIGHTING_OPEN
    ).select_related('category')

    pairs_entries = PairsEntry.objects.filter(
        Q(competitor_a=registration) | Q(competitor_b=registration)
    ).select_related('category', 'competitor_a__competitor', 'competitor_b__competitor')

    kata_entries = KataEntry.objects.filter(
        Q(tori=registration) | Q(uke=registration)
    ).select_related('category', 'tori__competitor', 'uke__competitor')

    team_entries = TeamEntry.objects.filter(
        members=registration
    ).select_related('category', 'dojo')

    context = {
        'event': registration.competition,
        'registration': registration,
        'competitor': registration.competitor,
        'slots': slots,
        'random_attack_entries': random_attack_entries,
        'ground_fighting_entries': ground_fighting_entries,
        'ground_fighting_open_entries': ground_fighting_open_entries,
        'pairs_entries': pairs_entries,
        'kata_entries': kata_entries,
        'team_entries': team_entries,
    }

    return HttpResponse(loader.get_template("schedule/registration_detail.html").render(context, request))


@require_access
def schedule_compact(request):
    """Compact schedule view for the active competition."""
    competitions = Competition.objects.filter(active=True).order_by("firstDay")
    competition = competitions.first()

    if competition is None:
        context = {'event': None, 'days': []}
        return HttpResponse(loader.get_template("schedule/schedule_compact.html").render(context, request))

    # Current time in Europe/Berlin (CET+1)
    now = datetime.now()

    # Get ExternalProvidedSlots - filter out past events
    external_slots = ExternalProvidedSlot.objects.filter(
        competition=competition,
        start__gte=now
    ).order_by('start', 'tatami')

    # Get manually created Slots (base Slot, not ExternalProvidedSlot) - filter out past events
    manual_slots = Slot.objects.filter(
        competition=competition,
        start__gte=now
    ).non_polymorphic().filter(
        polymorphic_ctype=ContentType.objects.get_for_model(Slot)
    ).order_by('start')

    # Group by date
    days = {}

    for slot in external_slots:
        day_key = slot.start.date()
        if day_key not in days:
            days[day_key] = []
        days[day_key].append({
            'id': slot.id,
            'start': slot.start,
            'discipline': slot.discipline,
            'category_name': slot.category_name,
            'tatami': slot.tatami,
            'type': slot.type,
            'is_external': True,
        })

    for slot in manual_slots:
        day_key = slot.start.date()
        if day_key not in days:
            days[day_key] = []
        days[day_key].append({
            'id': slot.id,
            'start': slot.start,
            'discipline': '',
            'category_name': slot.title,
            'tatami': None,
            'type': '',
            'is_external': False,
        })

    # Sort slots within each day by start time
    for day_key in days:
        days[day_key].sort(key=lambda s: s['start'])

    # Convert to list of dicts sorted by date
    days_list = [{'date': date, 'slots': slots} for date, slots in sorted(days.items())]

    context = {
        'event': competition,
        'days': days_list,
    }

    return HttpResponse(loader.get_template("schedule/schedule_compact.html").render(context, request))


@require_access
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