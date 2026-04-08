from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter
from .models import (
    Competition, Slot, ExternalProvidedSlot, Competitor, Registration, Rank, Dojo, Category,
    Entry, SingleCompetitorEntry, PairsEntry, KataEntry, TeamEntry
)


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'firstDay', 'lastDay', 'active', 'jjcmCompetitionId')
    list_filter = ('active',)
    readonly_fields = ('set_active_button',)

    def set_active_button(self, obj):
        if obj.pk:
            url = reverse('admin:competition-set-active', args=[obj.pk])
            if obj.active:
                return mark_safe('<span style="color: green; font-weight: bold;">This is the active competition</span>')
            return format_html(
                '<a class="button" href="{}">Set active competition</a>',
                url
            )
        return '-'
    set_active_button.short_description = 'Activation'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:competition_id>/set-active/',
                self.admin_site.admin_view(self.set_active_view),
                name='competition-set-active',
            ),
        ]
        return custom_urls + urls

    def set_active_view(self, request, competition_id):
        Competition.objects.exclude(pk=competition_id).update(active=False)
        Competition.objects.filter(pk=competition_id).update(active=True)
        self.message_user(request, "Competition set as active.")
        return HttpResponseRedirect(reverse('admin:schedule_competition_change', args=[competition_id]))

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:
            return (
                (None, {'fields': ('title', 'description', 'location', 'firstDay', 'lastDay', 'active', 'jjcmCompetitionId', 'jjcmHash')}),
                ('Actions', {'fields': ('set_active_button',)}),
            )
        return fieldsets


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
    list_display = ('name', 'mon', 'kyu', 'dan', 'color')
    ordering = ('dan', '-kyu', '-mon')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'competition', 'discipline', 'cardinality', 'jjcmCategoryId')
    list_filter = ('competition', 'discipline')
    ordering = ('competition', 'discipline', 'name')


# Entry Admin (Polymorphic)
class EntryChildAdmin(PolymorphicChildModelAdmin):
    base_model = Entry
    list_filter = ['competition__title']


@admin.register(SingleCompetitorEntry)
class SingleCompetitorEntryAdmin(EntryChildAdmin):
    base_model = SingleCompetitorEntry
    show_in_index = False
    list_display = ('jjcmEntryId', 'discipline', 'competitor', 'competition', 'dojo')
    list_filter = ('competition', 'discipline', 'dojo')


@admin.register(PairsEntry)
class PairsEntryAdmin(EntryChildAdmin):
    base_model = PairsEntry
    show_in_index = False
    list_display = ('jjcmEntryId', 'competitor_a', 'competitor_b', 'competition', 'dojo')
    list_filter = ('competition', 'dojo')


@admin.register(KataEntry)
class KataEntryAdmin(EntryChildAdmin):
    base_model = KataEntry
    show_in_index = False
    list_display = ('jjcmEntryId', 'tori', 'uke', 'competition', 'dojo')
    list_filter = ('competition', 'dojo')


@admin.register(TeamEntry)
class TeamEntryAdmin(EntryChildAdmin):
    base_model = TeamEntry
    show_in_index = False
    list_display = ('jjcmEntryId', 'dojo', 'competition', 'member_count')
    list_filter = ('competition', 'dojo')

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(Entry)
class EntryParentAdmin(PolymorphicParentModelAdmin):
    base_model = Entry
    child_models = (SingleCompetitorEntry, PairsEntry, KataEntry, TeamEntry)
    list_filter = (PolymorphicChildModelFilter, 'competition__title')
    list_display = ('jjcmEntryId', 'competition', 'dojo', 'entry_type')

    def entry_type(self, obj):
        return obj.get_real_instance_class().__name__
    entry_type.short_description = 'Type'