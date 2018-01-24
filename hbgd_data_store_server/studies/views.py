import re

from toolz.itertoolz import groupby

from django.db.models import Q
from django.views.generic.base import TemplateView
from django.core.urlresolvers import reverse
from django.views.generic.list import ListView
from django.views import View
from django.http import HttpResponseRedirect, Http404, HttpResponse
import django_tables2 as tables

from .dataframes import (
    get_counts_df,
    get_counts_by_domain,
    pivot_counts_df,
    get_variable_counts,
    get_variable_count_by_variable
)

from .forms import StudyFilterForm, VariableListForm, StudyExplorerForm
from .models import (
    StudyField,
    Study,
    StudyVariable,
    Domain,
    Variable,
    Filter,
)
from .plots import (
    get_summary_heatmap,
    get_heatmap,
    get_age_heatmap,
)
from .tables import StudyTable, VariableTable


class StudyListView(tables.SingleTableView):
    template_name = 'studies/study_list.html'
    table_class = StudyTable
    table_pagination = {
        'per_page': 20
    }

    def get_study_dict(self):
        study_fields = StudyField.objects.filter(big_order__gte=0) or StudyField.objects.all()
        df = StudyVariable.get_dataframe(study_field__in=study_fields)
        df['study_id'] = df.index
        df_dict = df.to_dict('records')

        for study_field in study_fields.filter(field_type='int'):
            for record in df_dict:
                if record[study_field.label]:
                    record[study_field.label] = int(float(record[study_field.label]))
        return df_dict

    def get_queryset(self, **kwargs):
        """
        Overrides existing table get_queryset method

        Returns:
            Dict(StudyVariable)
        """
        return self.get_study_dict()


class StudyFilterView(ListView):
    model = Study
    template_name = "studies/study_filter.html"
    paginate_by = 10

    def get_queryset(self, **kwargs):
        GET = self.request.GET

        filters = Filter.objects.filter(
            Q(study_field__in=GET.keys()) | Q(domain__code__in=GET.keys())
        )
        studies = Study.filter_studies(filters, GET)
        return studies

    def get(self, request):
        if 'Reset' in request.GET:
            return HttpResponseRedirect(reverse("study-filter"))

        # Filter empty GET queries
        new_GET = request.GET.copy()
        for name in request.GET:
            selections = [s for s in request.GET.getlist(name) if s]
            if not selections:
                new_GET.pop(name)
            else:
                new_GET.setlist(name, selections)

        # Filter full ranges
        filter_query = (Q(study_field__in=new_GET.keys()) | Q(domain__code__in=new_GET.keys()))
        slider_filters = Filter.objects.filter(filter_query).exclude(widget='checkbox')
        for filt in slider_filters:
            if filt.is_full_range(*new_GET.get(filt.name).split(';')):
                new_GET.pop(filt.name)

        # Drop Apply
        new_GET.pop('Apply', None)

        # Redirect if GET params have changed
        if new_GET != request.GET:
            redirect = reverse("study-filter")
            GET_string = new_GET.urlencode()
            if GET_string:
                redirect = '?'.join([redirect, GET_string])
            return HttpResponseRedirect(redirect)
        return super(StudyFilterView, self).get(request)

    def get_context_data(self, **kwargs):
        from bokeh.embed import components
        context = super(StudyFilterView, self).get_context_data(**kwargs)

        study_form = StudyFilterForm(request=self.request)

        context['study_form'] = study_form

        get = self.request.GET.copy()
        get.pop('page', None)
        get.pop('submit', None)

        context['GET_params'] = get.urlencode()

        context['n_total'] = Study.objects.count()

        study_ids = self.object_list.order_by('study_id').values_list('study_id', flat=True)
        context['filtered_studies'] = study_ids

        if self.object_list.count() > 0:
            context['field_names'], context['study_dict'] = self.get_study_dict()

        # Make summary plot
        df = get_counts_df(self.object_list)
        if len(df) > 0:
            summary_heatmap_df = get_counts_by_domain(df)
            summary_heatmap = get_summary_heatmap(summary_heatmap_df, study_ids)
            [bk_summary_script, bk_summary_div] = components(summary_heatmap)
            context['plot_summary_script'] = bk_summary_script
            context['plot_summary_div'] = bk_summary_div

        return context

    def get_study_dict(self):
        study_fields = StudyField.objects.filter(lil_order__gte=0).order_by('lil_order')
        if study_fields.count() == 0:
            return None, None
        studies = self.object_list
        df = StudyVariable.get_dataframe(study_field__in=study_fields, studies__in=studies)
        if df is None:
            return None, None
        ordered_labels = study_fields.values_list('label', flat=True)
        labels = [label for label in ordered_labels if label in df.columns]
        df_dict = df.to_dict('index')
        return labels, df_dict


class VariableListView(tables.SingleTableView):
    template_name = 'studies/variable_list.html'
    model = Variable
    table_class = VariableTable
    table_pagination = {
        'per_page': 50
    }

    def get(self, request, *args, **kwargs):
        if 'Reset' in request.GET:
            return HttpResponseRedirect(reverse("variable-list", kwargs=kwargs))
        self.domain = Domain.objects.get(code=kwargs.get('domain_code'))
        return super(VariableListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        qs = Variable.objects.filter(domain=self.domain)

        category = self.request.GET.get('category')
        variable = self.request.GET.get('variable')
        if category:
            qs = qs.filter(category=category)
        if variable:
            qs = qs.filter(Q(code=variable) | Q(label=variable))

        return qs

    def get_context_data(self, **kwargs):
        context = super(VariableListView, self).get_context_data(**kwargs)

        if not self.object_list.exclude(category=None):
            context['table'].exclude = ('category',)

        context['domains'] = Domain.objects.filter(is_qualifier=False).order_by('label')
        context['qualifiers'] = Domain.objects.filter(is_qualifier=True).order_by('label')
        context['domain'] = self.domain
        context['form'] = VariableListForm(request=self.request, domain=self.domain)

        return context


class StudyResolverMixin(object):

    def resolve_studies(self, context=None):
        """Resolve study filter query into study ids"""
        # TODO This could be much more efficient
        GET = self.request.GET
        if GET and 'study' not in GET:
            self.request.GET = GET.copy()
            filters = Filter.objects.filter(
                Q(study_field__in=GET.keys()) | Q(domain__code__in=GET.keys())
            )

            studies = Study.filter_studies(filters, GET)
            study_ids = studies.values_list('id', flat=True)
            self.request.GET.setlist('study', study_ids)

            if context is not None:
                applied_filters = [(filt.label, filt.get_applied_filters(GET)) for filt in filters]
                context['applied_filters'] = applied_filters
        else:
            study_ids = GET.getlist('study')
            studies = Study.objects.filter(id__in=study_ids)
        return studies


class StudyExplorerView(TemplateView, StudyResolverMixin):
    template_name = 'studies/study_explorer.html'

    def get(self, request):
        if 'Reset' in request.GET:
            return HttpResponseRedirect(reverse("study-explorer"))
        if 'study' in request.GET:
            if any(k for k in request.GET if k not in ['Apply', 'study', 'search']):
                raise Http404
        return super(StudyExplorerView, self).get(request)

    def get_context_data(self, **kwargs):
        from bokeh.embed import components

        context = super(StudyExplorerView, self).get_context_data(**kwargs)

        studies = self.resolve_studies(context)

        # Basic context
        context['form'] = StudyExplorerForm(request=self.request)
        context['n_total'] = Study.objects.count()
        context['n_selected'] = studies.count()

        df = get_counts_df(studies)
        if len(df) == 0:
            return context

        study_ids = studies.order_by('study_id').values_list('study_id', flat=True)

        # Make summary plot
        summary_heatmap_df = get_counts_by_domain(df)
        summary_heatmap = get_summary_heatmap(summary_heatmap_df, study_ids)
        [bk_summary_script, bk_summary_div] = components(summary_heatmap)
        context['plot_summary_script'] = bk_summary_script
        context['plot_summary_div'] = bk_summary_div

        # Make heatmaps
        domains = Domain.objects.all().order_by('label')
        domain_heatmaps = {}
        domain_age_heatmaps = {}
        active_domains = []
        active_age_domains = []

        # need for later, but storing for single query
        variables = Variable.objects.all()
        var_lookup = groupby('id', variables.values('id', 'label', 'code'))

        pivot_df = pivot_counts_df(df)

        for domain in domains:
            code = domain.code
            domain_heatmap_df = get_variable_counts(pivot_df, var_lookup, code)

            if domain_heatmap_df is not None:
                count = domain_heatmap_df['count'].sum()
                active_domains.append((count, domain))
                domain_heatmaps[domain.label] = get_heatmap(domain_heatmap_df, study_ids)

            domain_age_heatmap_df = get_variable_count_by_variable(pivot_df, var_lookup, code)

            if domain_age_heatmap_df is not None:
                count = domain_heatmap_df['count'].sum()
                active_age_domains.append((count, domain))
                domain_age_heatmaps[domain.label] = get_age_heatmap(domain_age_heatmap_df)

        [bk_script, bk_divs] = components(domain_heatmaps)
        [bk_age_script, bk_age_divs] = components(domain_age_heatmaps)
        context['plot_script'] = bk_script
        context['plot_age_script'] = bk_age_script

        # Build domains context
        domains_context = []
        for count, domain in active_domains:
            domains_context.append({
                "heatmap": bk_divs.get(domain.label),
                "id": domain.pk,
                "label": domain.label,
                "code": domain.code.strip("*"),
                "count": count,
            })
        context['domains'] = domains_context
        domains_age_context = []
        for count, domain in active_age_domains:
            domains_age_context.append({
                "age_heatmap": bk_age_divs.get(domain.label),
                "id": domain.pk,
                "label": domain.label,
                "code": domain.code.strip("*"),
                "count": count,
            })
        context['age_domains'] = domains_age_context
        return context


class BaseExportView(View, StudyResolverMixin):
    by_age = False

    def get(self, request, *args, **kwargs):
        studies = self.resolve_studies()
        domain = Domain.objects.get(pk=kwargs.get('domain_id'))
        df = get_counts_df(studies)
        pivot_df = pivot_counts_df(df)
        # need for later, but storing for single query
        variables = Variable.objects.all()
        var_lookup = groupby('id', variables.values('id', 'label', 'code'))
        if self.by_age is True:
            domain_df = get_variable_count_by_variable(pivot_df, var_lookup, domain.code)
        else:
            domain_df = get_variable_counts(pivot_df, var_lookup, domain.code)
        # Build response
        filename = self.get_filename(domain)
        content_type = 'text/csv'
        response = HttpResponse(content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
        domain_df.to_csv(response)
        return response


class ExportView(BaseExportView):
    by_age = False

    def get_filename(self, domain):
        pattern = re.compile(r'\s+')
        name = re.sub(pattern, '', domain.label)
        return "%s.csv" % name


class ExportByAgeView(BaseExportView):
    by_age = True

    def get_filename(self, domain):
        pattern = re.compile(r'\s+')
        name = re.sub(pattern, '', domain.label)
        return "%s_by_age.csv" % name
