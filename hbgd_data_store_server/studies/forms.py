import itertools
from collections import OrderedDict

from django import forms
from django.db.models import Case, When, Value, BooleanField

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div
from crispy_forms_foundation.layout import Layout, Fieldset
from crispy_forms_foundation.layout.containers import AccordionHolder, AccordionItem
from crispy_forms_foundation.layout.fields import InlineField, Field
from crispy_forms_foundation.layout.buttons import Submit, ButtonGroup
from crispy_forms_foundation.layout.grid import Row, Column

from .fields import (EmptyChoiceField, RangeField, DiscreteRangeField,
                     ExtendedMultipleChoiceField)
from .models import Study, Filter, Variable


class VariableListForm(forms.Form):
    category = EmptyChoiceField(required=False, empty_label="Search by Category")
    variable = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': 'Search by Variable'}
        ),
    )

    def __init__(self, *args, **kwargs):
        self._request = kwargs.pop('request')
        self._domain = kwargs.pop('domain')

        super(VariableListForm, self).__init__(*args, **kwargs)

        variables = Variable.objects.filter(domain=self._domain)

        # set category choices based on variable categories or disable field if None
        if not variables.exclude(category=None):
            self.fields['category'].disabled = True
        else:
            choices = list(variables.values_list('category', 'category')
                                    .distinct()
                                    .order_by('category'))
            self.fields['category'].choices = tuple(self.fields['category'].choices + choices)

        # set initial form fields based on request
        self.initial = dict(category=self._request.GET.get('category'),
                            variable=self._request.GET.get('variable'))

        # sorted, unique list of variable codes and labels for autocomplete tip
        self.variable_autocomplete_options = sorted(set(itertools
                                                    .chain(*variables
                                                        .values_list(
                                                            'code', 'label'))))

        self.helper = FormHelper()
        self.helper.form_method = "GET"
        self.helper.layout = Layout(
            Row(
                Column(
                    InlineField('category', label_class="hide", input_column="small-12"),
                    css_class="small-4",
                ),
                Column(
                    InlineField('variable', label_class="hide", input_column="small-12"),
                    css_class="small-8",
                )
            ),
            Row(
                Column(
                    ButtonGroup(
                        Submit('Submit', 'Submit', css_class="tiny"),
                        Submit('Reset', 'Clear Filters', css_class="secondary tiny")
                    )
                )
            ),
        )


class StudyExplorerForm(forms.Form):
    study = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Study.objects.all().order_by('study_id'),
        label=False
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': 'Select Study by Name'}
        ),
    )

    def __init__(self, *args, **kwargs):
        self._request = kwargs.pop('request')

        super(StudyExplorerForm, self).__init__(*args, **kwargs)

        # Returns [-1] if None because `annotate` method will return empty queryset if ids = []
        ids = self._request.GET.getlist('study', [-1])
        studies = Study.objects.annotate(
            is_active=Case(When(id__in=ids, then=Value(True)),
                           default=Value(False),
                           output_field=BooleanField())
        )
        self.fields["study"].queryset = studies.order_by('-is_active', 'study_id')

        self.initial = {"study": ids}

        # JQuery UI autocomplete requires object with label and value attrs
        # Have to augment id value by one because input checkbox ids start at one
        self.search_autocomplete_options = [
            dict(label=k['study_id'], value=k['study_id'], id=i + 1)
            for i, k in enumerate(self.fields["study"].queryset.values('id', 'study_id'))
        ]

        self.helper = FormHelper()
        self.helper.form_method = "GET"
        self.helper.layout = Layout(
            Row(
                Column(
                    InlineField('search', label_class="hide", input_column="small-12"),
                    css_class="small-12",
                )
            ),
            Row(
                Column(
                    Div(
                        HTML('<span id="message-bar">No new filters.</span>'),
                        ButtonGroup(
                            Submit('Apply', 'Apply', css_class="tiny secondary"),
                            Submit('Reset', 'Clear Filters', css_class="secondary tiny"),
                            css_class="right",
                        )
                    )
                ),
                css_id="sticky-menu"
            ),
            Row(
                Column(
                    Fieldset("Studies", 'study')
                ),
            ),
        )


class StudyFilterForm(forms.Form):
    accordion_template = 'forms/accordion-holder.html'
    range_template = 'forms/range-widget.html'
    domain_template = 'forms/domain-widget.html'

    def __init__(self, *args, **kwargs):
        self._request = kwargs.pop('request')

        super(StudyFilterForm, self).__init__(*args, **kwargs)

        self.applied_filters = []

        layouts = OrderedDict([('Study', []), ('Qualifier', []), ('Domain', [])])
        for filt in Filter.objects.all().order_by('label'):
            layout_item, form_field = self._get_filter_layout_and_field(filt)
            # put layout_item into correct layout_group
            layouts[filt.filter_type].append(layout_item)
            # register form_field in form fields
            self.fields[filt.name] = form_field
            # add pretty_initial values to form attr if exists (for view)
            if hasattr(form_field, 'pretty_initial'):
                self.applied_filters.append((filt.label, form_field.pretty_initial))

        study_layout = self._get_accordion_or_empty(items=layouts['Study'])
        qualifier_layout = self._get_accordion_or_empty(items=layouts['Qualifier'])
        domain_layout = self._get_accordion_or_empty(items=layouts['Domain'])

        self.helper = FormHelper()
        self.helper.form_method = "GET"
        self.helper.layout = Layout(
            Row(
                Column(
                    Div(
                        HTML('<span id="message-bar">No new filters.</span>'),
                        ButtonGroup(
                            Submit('Apply', 'Apply', css_class="tiny secondary"),
                            Submit('Reset', 'Clear Filters', css_class="secondary tiny"),
                            css_class="right",
                        )
                    )
                ),
                css_id="sticky-menu"
            ),
            Row(
                Column(
                    Fieldset("Study metadata", study_layout),
                )
            ),
            Row(
                Column(
                    Fieldset("Qualifier metadata", qualifier_layout),
                )
            ),
            Row(
                Column(
                    Fieldset("Domain metadata", domain_layout),
                )
            )
        )

    def _get_accordion_or_empty(self, items=()):
        if items:
            field = AccordionHolder(*items, template=self.accordion_template)
        else:
            field = HTML("Please contact your administrator about adding a filter.")
        return field

    def _get_filter_layout_and_field(self, filt):
        """
        Initializes the appropriate crispy form layout and form field
        object given a Filter.

        Parameters:
            filt: Filter
                A Filter model instance

        Returns:
            crispy_forms_foundation.layout.Field, django.forms.Field
        """

        layout_field = Field(filt.name)
        field_kwargs = dict(required=False, label=False)
        values = filt.get_values()

        if filt.widget == 'discrete slider':
            layout_field.template = self.range_template
            initial = filt.get_initial_slider_values(self._request.GET, values=values)
            field_kwargs.update(initial)
            choices = filt.get_choices(values=values)
            form_field = DiscreteRangeField(choices=choices,
                                            custom_json=filt.widget_json,
                                            **field_kwargs)

        elif filt.widget == 'double slider':
            layout_field.template = self.range_template
            initial = filt.get_initial_slider_values(self._request.GET)
            field_kwargs.update(initial)
            form_field = RangeField(min_value=values[0],
                                    max_value=values[-1],
                                    custom_json=filt.widget_json,
                                    **field_kwargs)

        else:
            widget = forms.CheckboxSelectMultiple()
            choices = filt.get_choices(values=values, include_ids=True)
            ids, values, labels = zip(*choices) if len(choices) else ([], [], [])
            counts = filt.get_counts(self._request, values=values)
            initial = self._request.GET.getlist(filt.name)

            if filt.domain and not filt.domain.is_qualifier:
                layout_field.template = self.domain_template
                form_field = ExtendedMultipleChoiceField(
                    widget=widget,
                    choices=choices,
                    initial=initial,
                    counts=counts,
                    autocomplete=sorted(set(values) | set(labels)),
                    categories=filt.get_categories(),
                    **field_kwargs
                )

            else:
                form_field = ExtendedMultipleChoiceField(
                    widget=widget,
                    counts=counts,
                    choices=choices,
                    initial=initial,
                    **field_kwargs
                )

        if initial:
            form_field.pretty_initial = filt.get_applied_filters(self._request.GET)

        active = True if initial else False
        layout_item = AccordionItem(filt.label, layout_field, active=active)
        return layout_item, form_field
