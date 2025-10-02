from django.http import HttpResponse
from django.template import loader
from django.contrib.contenttypes.models import ContentType

import json
from datetime import datetime

from .models import Event, Slot, ExternalProvidedSlot

def event_board(request):
    next_event = Event.objects.filter(active=True).order_by("firstDay")[0]
    # slots = Slot.objects.filter(event=next_event).order_by("start_time").all()

    non_competition_slots = Slot.objects.filter(event=next_event).exclude(polymorphic_ctype=ContentType.objects.get_for_model(ExternalProvidedSlot)).all()
    competition_slots = ExternalProvidedSlot.objects.filter(event=next_event).order_by("start").order_by("tatami").all()
   
    last_group = ""
    slot_list = []
    group_node = None

    for slot in competition_slots:
        # slot.started = False

        # if (slot.start > datetime.now()):
        #     slot.started = True

        slot.title = slot.category_name

        if last_group != f"{slot.discipline} {slot.tatami}":
            last_group = f"{slot.discipline} {slot.tatami}"
            group_node = None

        if group_node is None:
            group_node = { 'type': 'group', 'title': slot.discipline, 'start': slot.start, 'tatami': slot.tatami, 'slots': [] }
            slot_list.append(group_node)

        slot.type = 'subitem'
        group_node["slots"].append(slot)

    for slot in non_competition_slots:
        slot.type = 'item'
        slot_list.append(slot)

    def extract_start(slot):
        try:
            return slot['start'] # the json way...
        except:
            return slot.start # the django model way...

    slot_list.sort( key=extract_start )

    context = { 'event': next_event, 'slots': slot_list }

    return HttpResponse( loader.get_template("schedule/event_board.html").render(context, request))