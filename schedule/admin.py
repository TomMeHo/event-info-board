from django.contrib import admin
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter
from io import StringIO
from .models import (
    Competition, Slot, ExternalProvidedSlot, Competitor, Registration, Rank, Dojo, Category,
    Entry, SingleCompetitorEntry, PairsEntry, KataEntry, TeamEntry
)


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'firstDay', 'lastDay', 'active', 'jjcmCompetitionId')
    list_filter = ('active',)
    readonly_fields = ('set_active_button', 'refresh_buttons')

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

    def refresh_buttons(self, obj):
        if obj.pk and obj.jjcmCompetitionId:
            buttons = []
            actions = [
                ('refresh-all', 'Refresh All', '#417690'),
                ('refresh-all-force', 'Force Refresh All', '#ba2121'),
                ('refresh-schedule', 'Schedule', '#79aec8'),
                ('refresh-competitors', 'Competitors', '#79aec8'),
                ('refresh-entries', 'Entries', '#79aec8'),
                ('refresh-categories', 'Categories', '#79aec8'),
            ]
            for action, label, color in actions:
                url = reverse(f'admin:competition-{action}', args=[obj.pk])
                buttons.append(
                    f'<a class="button" style="background-color: {color}; margin-right: 5px;" href="{url}">{label}</a>'
                )
            return mark_safe(' '.join(buttons))
        return mark_safe('<span style="color: gray;">Save with a JJCM Competition ID to enable refresh</span>')
    refresh_buttons.short_description = 'Refresh Data from JJCM'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:competition_id>/set-active/',
                self.admin_site.admin_view(self.set_active_view),
                name='competition-set-active',
            ),
            path(
                '<int:competition_id>/refresh-all/',
                self.admin_site.admin_view(self.refresh_all_view),
                name='competition-refresh-all',
            ),
            path(
                '<int:competition_id>/refresh-all-force/',
                self.admin_site.admin_view(self.refresh_all_force_view),
                name='competition-refresh-all-force',
            ),
            path(
                '<int:competition_id>/refresh-schedule/',
                self.admin_site.admin_view(self.refresh_schedule_view),
                name='competition-refresh-schedule',
            ),
            path(
                '<int:competition_id>/refresh-competitors/',
                self.admin_site.admin_view(self.refresh_competitors_view),
                name='competition-refresh-competitors',
            ),
            path(
                '<int:competition_id>/refresh-entries/',
                self.admin_site.admin_view(self.refresh_entries_view),
                name='competition-refresh-entries',
            ),
            path(
                '<int:competition_id>/refresh-categories/',
                self.admin_site.admin_view(self.refresh_categories_view),
                name='competition-refresh-categories',
            ),
        ]
        return custom_urls + urls

    def set_active_view(self, request, competition_id):
        Competition.objects.exclude(pk=competition_id).update(active=False)
        Competition.objects.filter(pk=competition_id).update(active=True)
        self.message_user(request, "Competition set as active.")
        return HttpResponseRedirect(reverse('admin:schedule_competition_change', args=[competition_id]))

    def _get_jjcm_id(self, competition_id):
        competition = Competition.objects.get(pk=competition_id)
        return competition.jjcmCompetitionId

    def refresh_all_view(self, request, competition_id):
        jjcm_id = self._get_jjcm_id(competition_id)
        out = StringIO()
        try:
            call_command('getAll', str(jjcm_id), stdout=out, stderr=out)
            self.message_user(request, f"Successfully refreshed all data for competition.")
        except Exception as e:
            self.message_user(request, f"Error refreshing data: {e}", level='error')
        return HttpResponseRedirect(reverse('admin:schedule_competition_change', args=[competition_id]))

    def refresh_all_force_view(self, request, competition_id):
        jjcm_id = self._get_jjcm_id(competition_id)
        out = StringIO()
        try:
            call_command('getAll', str(jjcm_id), '--force', stdout=out, stderr=out)
            self.message_user(request, f"Successfully force-refreshed all data for competition.")
        except Exception as e:
            self.message_user(request, f"Error refreshing data: {e}", level='error')
        return HttpResponseRedirect(reverse('admin:schedule_competition_change', args=[competition_id]))

    def refresh_schedule_view(self, request, competition_id):
        jjcm_id = self._get_jjcm_id(competition_id)
        out = StringIO()
        try:
            call_command('getSchedule', str(jjcm_id), stdout=out, stderr=out)
            self.message_user(request, f"Successfully refreshed schedule.")
        except Exception as e:
            self.message_user(request, f"Error refreshing schedule: {e}", level='error')
        return HttpResponseRedirect(reverse('admin:schedule_competition_change', args=[competition_id]))

    def refresh_competitors_view(self, request, competition_id):
        jjcm_id = self._get_jjcm_id(competition_id)
        out = StringIO()
        try:
            call_command('getCompetitors', str(jjcm_id), stdout=out, stderr=out)
            self.message_user(request, f"Successfully refreshed competitors.")
        except Exception as e:
            self.message_user(request, f"Error refreshing competitors: {e}", level='error')
        return HttpResponseRedirect(reverse('admin:schedule_competition_change', args=[competition_id]))

    def refresh_entries_view(self, request, competition_id):
        jjcm_id = self._get_jjcm_id(competition_id)
        out = StringIO()
        try:
            call_command('getEntries', str(jjcm_id), stdout=out, stderr=out)
            self.message_user(request, f"Successfully refreshed entries.")
        except Exception as e:
            self.message_user(request, f"Error refreshing entries: {e}", level='error')
        return HttpResponseRedirect(reverse('admin:schedule_competition_change', args=[competition_id]))

    def refresh_categories_view(self, request, competition_id):
        jjcm_id = self._get_jjcm_id(competition_id)
        out = StringIO()
        try:
            call_command('getCategories', str(jjcm_id), stdout=out, stderr=out)
            self.message_user(request, f"Successfully refreshed categories.")
        except Exception as e:
            self.message_user(request, f"Error refreshing categories: {e}", level='error')
        return HttpResponseRedirect(reverse('admin:schedule_competition_change', args=[competition_id]))

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:
            return (
                (None, {'fields': ('title', 'description', 'location', 'firstDay', 'lastDay', 'active', 'jjcmCompetitionId', 'jjcmHash')}),
                ('Actions', {'fields': ('set_active_button', 'refresh_buttons')}),
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

    def add_view(self, request, form_url='', extra_context=None):
        # Skip type selection, go directly to adding base Slot
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(Slot, for_concrete_model=False)
        if 'ct_id' not in request.GET:
            new_get = request.GET.copy()
            new_get['ct_id'] = str(ct.pk)
            request.GET = new_get
        return super().add_view(request, form_url, extra_context)


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
    list_display = ('jjcmEntryId', 'discipline', 'competitor', 'category', 'result', 'competition')
    list_filter = ('competition', 'discipline', 'category')


@admin.register(PairsEntry)
class PairsEntryAdmin(EntryChildAdmin):
    base_model = PairsEntry
    show_in_index = False
    list_display = ('jjcmEntryId', 'competitor_a', 'competitor_b', 'category', 'result', 'competition')
    list_filter = ('competition', 'category')


@admin.register(KataEntry)
class KataEntryAdmin(EntryChildAdmin):
    base_model = KataEntry
    show_in_index = False
    list_display = ('jjcmEntryId', 'tori', 'uke', 'category', 'result', 'competition')
    list_filter = ('competition', 'category')


@admin.register(TeamEntry)
class TeamEntryAdmin(EntryChildAdmin):
    base_model = TeamEntry
    show_in_index = False
    list_display = ('jjcmEntryId', 'dojo', 'member_count', 'category', 'result', 'competition')
    list_filter = ('competition', 'category')

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(Entry)
class EntryParentAdmin(PolymorphicParentModelAdmin):
    base_model = Entry
    child_models = (SingleCompetitorEntry, PairsEntry, KataEntry, TeamEntry)
    list_filter = (PolymorphicChildModelFilter, 'competition__title', 'category')
    list_display = ('jjcmEntryId', 'competition', 'category', 'result', 'entry_type')

    def entry_type(self, obj):
        return obj.get_real_instance_class().__name__
    entry_type.short_description = 'Type'