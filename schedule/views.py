from django.http import HttpResponse
from django.template import loader

from datetime import datetime

from .models import Event, Slot

def event_board(request):
    next_event = Event.objects.filter(date__gte=datetime.now()).order_by("date")[0]
    slots = Slot.objects.filter(event=next_event).order_by("start_time").all()

    for slot in slots:
        slot.started = False
        if (slot.start_time > datetime.now().time):
            slot.started = True

    context = { 'event': next_event, 'slots': slots }

    return HttpResponse( loader.get_template("schedule/event_board.html").render(context, request))