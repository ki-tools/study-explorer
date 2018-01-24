from django.conf.urls import url
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from .admin_views import ImportStudiesView, ImportIDXView
from .models import (
    StudyField,
    Study,
    StudyVariable,
    Variable,
    Count,
    Domain,
    Filter,
)


class IsVisibleListFilter(admin.SimpleListFilter):
    title = _('Display')
    parameter_name = 'display'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('lil_order', _('Study Filter page')),
            ('big_order', _('Study List page')),
            ('either', _('Study Filter OR Study List page')),
            ('both', _('Study Filter AND Study List pages')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == 'lil_order':
            return queryset.filter(lil_order__gte=0).order_by('lil_order')
        elif self.value() == 'big_order':
            return queryset.filter(big_order__gte=0).order_by('big_order')
        elif self.value() == 'either':
            return queryset.filter(Q(big_order__gte=0) | Q(lil_order__gte=0))
        elif self.value() == 'both':
            return (queryset.filter(big_order__gte=0, lil_order__gte=0)
                            .order_by('lil_order', 'big_order'))


class StudyFieldAdmin(admin.ModelAdmin):

    list_display = ('label', 'field_name', 'field_type', 'lil_order', 'big_order')
    readonly_fields = ('field_name',)
    fields = ('field_name', 'label', 'field_type', 'lil_order', 'big_order')
    list_filter = ('field_type', IsVisibleListFilter)


class StudyVariableAdmin(admin.ModelAdmin):

    list_display = ('study_ids', 'study_field', 'value',)
    list_filter = ('study_field',)

    def study_ids(self, obj):
        study_ids = [str(study) for study in obj.studies.all()]
        return ' | '.join(study_ids)
    study_ids.short_description = 'Study IDs'


class StudyAdmin(admin.ModelAdmin):

    list_display = ('study_id',)
    readonly_fields = ('study_id',)

    def get_urls(self):
        urls = super(StudyAdmin, self).get_urls()
        extra_urls = [
            url(
                r'^import_studies/$',
                ImportStudiesView.as_view(),
                name='import-studies'),
        ]
        return extra_urls + urls


class VariableAdmin(admin.ModelAdmin):

    list_display = ('domain', 'category', 'code', 'label')

    list_filter = ('domain', 'category')


class DomainAdmin(admin.ModelAdmin):

    list_display = ('code', 'label', 'is_qualifier')


class FilterAdmin(admin.ModelAdmin):

    list_display = ('label', 'domain', 'study_field', 'widget')


class CountAdmin(admin.ModelAdmin):

    list_display = ('study', 'variables', 'count')

    def variables(self, obj):
        codes = [str(code) for code in obj.codes.all()]
        return ' | '.join(codes)
    variables.short_description = 'Variables'

    def get_urls(self):
        urls = super(CountAdmin, self).get_urls()
        extra_urls = [
            url(
                r'^import_idx/$',
                ImportIDXView.as_view(),
                name='import-idx'),
        ]
        return extra_urls + urls


admin.site.register(StudyField, StudyFieldAdmin)
admin.site.register(StudyVariable, StudyVariableAdmin)
admin.site.register(Study, StudyAdmin)
admin.site.register(Variable, VariableAdmin)
admin.site.register(Domain, DomainAdmin)
admin.site.register(Count, CountAdmin)
admin.site.register(Filter, FilterAdmin)
