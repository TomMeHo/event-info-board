from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter
from .models import Competition, Slot, ExternalProvidedSlot, Competitor, Registration, Rank, Dojo

admin.site.register(Competition)


class SlotChildAdmin(PolymorphicChildModelAdmin):
    base_model = Slot
    list_filter = ['competition__title']


@admin.register(ExternalProvidedSlot)
class ExternalProvidedSlotAdmin(SlotChildAdmin):
    base_model = ExternalProvidedSlot
    show_in_index = False
    list_display = ('title', 'competition', 'discipline', 'category_name', 'start')


@admin.register(Slot)
class SlotParentAdmin(PolymorphicParentModelAdmin):
    base_model = Slot
    child_models = (Slot, ExternalProvidedSlot)
    list_filter = (PolymorphicChildModelFilter, 'competition__title')
    list_display = ('title', 'competition', 'start', 'slot_type')

    def slot_type(self, obj):
        return obj.get_real_instance_class().__name__


@admin.register(Competitor)
class CompetitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'givenName', 'sex', 'jjcmCompetitorId')


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('competitor', 'competition', 'dojo', 'jjcmRankId', 'jjcmRegistrationId')
    list_filter = ('competition', 'dojo', 'jjcmRankId')


@admin.register(Dojo)
class DojoAdmin(admin.ModelAdmin):
    list_display = ('jjcmDojoId', 'name')


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ('name', 'kyu', 'dan')
    ordering = ('dan', '-kyu')