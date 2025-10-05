from django.http import HttpResponse
from django.template import loader
from django.contrib.contenttypes.models import ContentType

import json
from datetime import datetime

from .models import Event, Slot, ExternalProvidedSlot

def event_board(request):
    event = Event.objects.filter(active=True).order_by("firstDay")[0]

    #TODO add second day
    
    non_competition_slots = Slot.objects.filter(event=event).filter(start__date=event.firstDay).exclude(polymorphic_ctype=ContentType.objects.get_for_model(ExternalProvidedSlot)).all()
    competition_slots = ExternalProvidedSlot.objects.filter(event=event).filter(start__date=event.firstDay).order_by("start").order_by("tatami").all()
   
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


    context = { 'event': event, 'day': event.firstDay, 'days': [{ 'slots': combined_slots }] } 

    return HttpResponse( loader.get_template("schedule/event_board.html").render(context, request))