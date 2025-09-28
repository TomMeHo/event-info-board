from django.contrib import admin
from .models import Event, Slot, DisplayTextPattern, ExternalProvidedSlot

# TODO make polymorphic admin interface

admin.site.register(Event)
admin.site.register(Slot)
admin.site.register(ExternalProvidedSlot)
admin.site.register(DisplayTextPattern)