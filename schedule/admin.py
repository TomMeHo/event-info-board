from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter
from .models import Event, Slot, ExternalProvidedSlot

admin.site.register(Event)

class SlotChildAdmin(PolymorphicChildModelAdmin):
    base_model = Slot
    list_filter = ['event__title']

@admin.register(ExternalProvidedSlot)
class ExternalProvidedSlotAdmin(SlotChildAdmin):
    base_model = ExternalProvidedSlot
    show_in_index = False
    list_display = ('title', 'event', 'discipline', 'category_name', 'start')

@admin.register(Slot)
class SlotParentAdmin(PolymorphicParentModelAdmin):
    base_model = Slot
    child_models = (Slot, ExternalProvidedSlot)
    list_filter = (PolymorphicChildModelFilter, 'event__title')
    list_display = ('title', 'event', 'start', 'slot_type')

    def slot_type(self, obj):
        return obj.get_real_instance_class().__name__
