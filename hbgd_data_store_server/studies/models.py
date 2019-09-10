# Copyright 2017-present, Bill & Melinda Gates Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import Counter

import pandas as pd

from django.db import models
from django.db.models import Q
from django.forms import ValidationError
from django.contrib.postgres import fields as pgfields

# Values that indicate a missing value
EMPTY_IDENTIFIERS = ['NaN', '.', 'None', 9999, None]

WIDGETS = [('checkbox', 'Checkboxes'), ('double slider', 'Double Slider'),
           ('discrete slider', 'Discrete Slider')]

FIELD_TYPES = [('list', 'List'), ('int', 'Integer'),
               ('str', 'Character String'), ('float', 'Decimal Number')]


def is_list(val, sep=','):
    """Checks if type can be cast to list, which is true for all types"""
    return True


def is_digit(val):
    """Checks if type can be cast to numeric value"""
    try:
        float(val)
        return True
    except ValueError:
        return False


def is_int(val):
    """Checks if type can be cast to numeric value"""
    try:
        if float(val).is_integer():
            return True
        else:
            return False
    except ValueError:
        return False


class StudyField(models.Model):

    field_name = models.CharField(
        max_length=50, unique=True, verbose_name='Field Name',
        help_text='Column header name as it appears in study import file.')

    label = models.CharField(
        max_length=100, null=True, blank=True, verbose_name='Label',
        help_text='Field name as it should appear in this app (spaces allowed).')

    field_type = models.CharField(
        max_length=10, choices=FIELD_TYPES, default='str', verbose_name='Field Type',
        help_text='Type of values that will go in this field.')

    big_order = models.IntegerField(
        default=-1, verbose_name='Large Display Order',
        help_text=('Order in which this field will be diplayed on study list '
                   '(negative value indicates field not shown).'))

    lil_order = models.IntegerField(
        default=-1, verbose_name='Small Display Order',
        help_text=('Order in which this field will be diplayed on study filter '
                   '(negative value indicates field not shown).'))

    class Meta:
        verbose_name_plural = "Study Fields"

    def save(self, **kwargs):
        if not self.label:
            self.label = self.field_name.replace('_', ' ')
        if self.field_type == 'list':
            for obj in StudyVariable.objects.filter(study_field=self):
                StudyVariable.split_list(obj)
        super(StudyField, self).save()

    def __str__(self):
        return self.label

    def clean(self):
        super(StudyField, self).clean()
        if self.field_type == 'str':
            return
        values = self.get_values()
        error = 'Pre-exiting {0} values could not be cast to {1}s'.format(
            self, dict(FIELD_TYPES).get(self.field_type))
        if self.field_type == 'float':
            if any(not is_digit(v) for v in values):
                raise ValidationError(error)
        elif self.field_type == 'int':
            if any(not is_int(v) for v in values):
                raise ValidationError(error)
        elif self.field_type == 'list':
            if all(not is_list(v) for v in values):
                raise ValidationError(error)

    def get_values(self):
        """
        Returns a list of valid values for the StudyField.

        Returns:
            list(str)
        """

        values = (StudyVariable.objects.filter(study_field=self)
                                       .values_list('value', flat=True)
                                       .distinct()
                                       .order_by('value'))

        values = [v for v in values if v not in EMPTY_IDENTIFIERS]
        return values


class Study(models.Model):

    study_id = models.CharField(
        max_length=50, unique=True, verbose_name='Study ID',
        help_text='Unique ID to reference the study.', db_index=True)

    class Meta:
        verbose_name_plural = "Studies"

    def __str__(self):
        return self.study_id

    @classmethod
    def filter_studies(self, filters, GET):
        """
        Returns studies with filters applied using AND join.

        Parameters:
            filters (queryset of Filter objects to apply)
            GET (GET request params)
        Returns:
            queryset of Study objects
        """
        studies = self.objects.all()
        if not filters:
            return studies
        set_list = [set(filt.filter_queryset(studies, GET)
                            .values_list('study_id', flat=True)) for filt in filters]

        study_ids = set.intersection(*set_list)
        studies = studies.filter(study_id__in=study_ids)

        return studies


class StudyVariable(models.Model):

    studies = models.ManyToManyField(
        Study, blank=True,
        help_text='The studies that this variable applies to.',
        db_index=True,
    )

    study_field = models.ForeignKey(
        StudyField, on_delete=models.CASCADE, to_field='field_name',
        help_text='The study field that this variable applies to.',
        db_index=True,
    )

    value = models.CharField(
        max_length=300, verbose_name='Value',
        help_text='The value of this study variable')

    class Meta:
        unique_together = ('value', 'study_field',)
        verbose_name_plural = "Study Variables"

    def __str__(self):
        return '{0}: {1}'.format(self.study_field, self.value)

    def clean(self):
        super(StudyVariable, self).clean()
        if self.study_field.field_type in ['str', 'list']:
            return
        error = '{0} cannot be cast to {1} type'.format(
            self, dict(FIELD_TYPES).get(self.study_field.field_type))
        if self.study_field.field_type == 'int':
            if not is_int(self.value):
                raise ValidationError(error)
        if self.study_field.field_type == 'float':
            if not is_digit(self.value):
                raise ValidationError(error)

    def save(self, *args, **kwargs):
        super(StudyVariable, self).save(*args, **kwargs)
        if self.study_field.field_type == 'list':
            StudyVariable.split_list(self)

    @classmethod
    def split_list(self, obj, sep=','):
        """
        Creates study variables by splitting a study variable with field type
        list into separate study variable items and deleting old study variable.

        Parameters:
            obj (object of type StudyVariable)
            sep (list separator - default: ',')
        """
        if sep not in obj.value:
            return
        for val in obj.value.split(sep):
            v = val.replace(' ', '')
            study_var, _ = self.objects.get_or_create(study_field=obj.study_field,
                                                      value=str(v))
            study_var.studies.add(*[s for s in obj.studies.all()])

    @classmethod
    def get_dataframe(self, **kwargs):
        """
        Returns a pandas.DataFrame of prettified `StudyVariables.values` with
        `Study.study_ids` as index and `StudyField.labels` as columns.

        Parameters:
            **kwargs (query filter to use on `StudyVariable`, must include
                      `study_field__in`)
        Returns:
            pandas.DataFrame(mixed dtype of object and float)
        """
        study_variables = self.objects.filter(**kwargs)
        if not study_variables:
            return
        study_fields = kwargs['study_field__in']

        study_var_dict = study_variables.values('studies__study_id', 'study_field', 'value')
        df = pd.DataFrame.from_records(study_var_dict)
        pivot = pd.pivot_table(df, index='studies__study_id',
                               columns='study_field', values='value',
                               aggfunc=(lambda x: max(x, key=len)))

        pivot = pivot.rename(columns=dict(study_fields.values_list('field_name', 'label')))

        # clean up floats and ints
        for study_field in study_fields.filter(field_type__in=['float', 'int']):
            name = study_field.label
            if name not in pivot.columns:
                continue
            pivot[name] = pivot[name].astype(float)
            if study_field.field_type == 'int':
                pivot[name] = pivot[name].map('{:.0f}'.format)
                pivot[name] = pivot[name].where(pivot[name] != 'nan', None)

        return pivot.where(pivot.notnull(), None)


class Domain(models.Model):

    code = models.CharField(
        max_length=10, verbose_name='Code', unique=True,
        help_text='Short identifying code to classify a condition.',
        db_index=True,
    )

    label = models.CharField(
        max_length=100, verbose_name='Label',
        help_text='Descriptive name for the condition.')

    is_qualifier = models.BooleanField(
        default=False,
        help_text='Declares whether the domain defines a qualifier')

    class Meta:
        verbose_name_plural = "domains"

    def __str__(self):
        return self.code


class FilterManager(models.Manager):
    def get_queryset(self):
        return super(FilterManager, self).get_queryset().select_related('study_field', 'domain')


class Filter(models.Model):
    objects = FilterManager()

    domain = models.ForeignKey(Domain, verbose_name='Domain',
                               null=True, blank=True, help_text="""
       The domain the condition falls under. Must supply either domain
       or study_field not both.""", db_index=True)

    label = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='A readable label for the Filter.')

    study_field = models.ForeignKey(
        StudyField, null=True, blank=True, to_field='field_name',
        on_delete=models.CASCADE, verbose_name='Study Field',
        help_text='The study field that this filter applies to.')

    widget = models.CharField(
        default='checkbox', choices=WIDGETS, max_length=20, help_text="""
        The widget used to display the filter""")

    widget_json = pgfields.JSONField(
        default=dict, blank=True, verbose_name='Widget JSON', help_text="""
        Specifies options to customize the widget as JSON.""")

    class Meta:
        unique_together = ('domain', 'study_field',)

    def save(self, **kwargs):
        if not self.label:
            self.label = self.domain.label if self.domain else self.study_field.label
        super(Filter, self).save()

    def clean(self):
        super(Filter, self).clean()
        if self.widget == 'double slider':
            values = self.get_values()
            if any(not is_digit(v) for v in values if v is not None):
                raise ValidationError('Filter values are not numeric, cannot '
                                      'use range slider widget')
        if self.domain and self.study_field:
            raise ValidationError('Supply either a domain or a study_field, not both.')

    @property
    def filter_type(self):
        """
        Return the type of the Filter

        Returns:
            str
        """
        if self.study_field:
            return 'Study'
        else:
            if self.domain.is_qualifier:
                return 'Qualifier'
            return 'Domain'

    @property
    def name(self):
        """
        Returns the name of the filter as determined by the study_field
        or domain code.

        Returns:
            str
        """
        return self.study_field.field_name if self.study_field else self.domain.code

    def get_values(self):
        """
        Returns a sorted list of valid code values for the Filter.

        Returns:
            list(str, int)
        """

        if self.study_field:
            values = self.study_field.get_values()
        else:
            values = (Variable.objects.filter(domain=self.domain)
                                      .values_list('code', flat=True)
                                      .distinct()
                                      .order_by('label'))

            # handle qualifier code str -> int hackery
            if self.domain.is_qualifier:
                values = sorted(values, key=lambda x: int(x))

        values = [v for v in values if v not in EMPTY_IDENTIFIERS]
        return values

    def get_choices(self, values=None, include_ids=False):
        """
        Returns a list of tuples of the valid choices for this
        Filter consisting of tuples of the code and label of each
        choice.

        Parameters:
            values (list(str, int)) - optionally pass in values
            include_ids (bool) - Include the model IDs in the choices

        Returns:
            list(tuple)
        """
        if values is None:
            values = self.get_values()

        if self.study_field:
            labels = values
            if include_ids:
                variables = StudyVariable.objects.filter(study_field=self.study_field)
                id_lookup = {var.value: var.id for var in variables}
        else:
            variables = Variable.objects.filter(domain=self.domain, code__in=values)
            var_lookup = {v.code: v.label for v in variables}
            id_lookup = {var.code: var.id for var in variables}
            labels = [var_lookup[v] for v in values]

        if include_ids:
            ids = [id_lookup[v] for v in values]
            return list(zip(ids, values, labels))
        else:
            return list(zip(values, labels))

    def get_counts(self, request, values=None):
        """
        Returns a count of related studies for each variable, sorted by
        `get_value`.

        Parameters:
            request (django.core.handlers.wsgi.WSGIRequest)
            values (list(str, int)) - optionally pass in values

        Returns:
            list(int)
        """

        GET = request.GET.copy().dict()

        # Remove 'self' filter from filter dict so that counts are inter-domain union
        GET.pop(self.name, None)
        filters = Filter.objects.filter(
            Q(study_field__in=GET.keys()) | Q(domain__code__in=GET.keys())
        )
        studies = Study.filter_studies(filters, request.GET)

        if self.study_field:
            variables = list(studies.filter(studyvariable__study_field=self.study_field)
                                    .values_list('studyvariable__value', flat=True))

        else:
            variables = [variable["code"] for variable
                         in (Variable.objects.filter(domain=self.domain,
                                                     count__study__in=studies)
                                             .values('count__study__study_id', 'code')
                                             .distinct())]

        counter = Counter(variables)

        if not values:
            values = self.get_values()

        counts = [counter[v] for v in values]

        return counts

    def get_categories(self):
        """
        Returns a list of categories for the filter domain. If all categories
        are None, returns an empty list.

        Returns:
            list(str)
        """
        if self.study_field:
            raise ValueError
        elif self.domain.is_qualifier:
            raise ValueError
        else:
            categories = (Variable.objects.filter(domain=self.domain)
                                          .values_list('category', flat=True)
                                          .order_by('label'))

        if not all(c in ["", None] for c in categories):
            return list(categories)
        else:
            return []

    def get_selections(self, GET, values=None):
        """
        Parses passed GET url parameters to values for filtering

        Parameters:
            GET (request.GET)
            values (list(str, int)) - optionally pass in values

        Returns:
            list(str)
        """
        if self.widget == "checkbox":
            selections = GET.getlist(self.name)
        elif self.widget == "discrete slider":
            choices = self.get_choices(values=values)
            values = list(zip(*choices))[0]
            labels = list(zip(*choices))[1]
            from_value, to_value = GET.get(self.name).split(';')
            from_index, to_index = labels.index(from_value), labels.index(to_value)
            selections = list(values[from_index:to_index + 1])
        elif self.widget == 'double slider':
            if not values:
                values = self.get_values()
            from_value, to_value = GET.get(self.name).split(';')
            selections = [v for v in values if
                          float(from_value) <= float(v) <= float(to_value)]
        else:
            raise ValueError
        return selections

    def filter_queryset(self, studies, GET):
        """
        Filters a Study QuerySet using the passed GET url parameters

        Parameters:
            studies (django.db.models.query.QuerySet)
            GET (request.GET)

        Returns:
            django.db.models.query.QuerySet
        """
        selections = self.get_selections(GET)

        if self.study_field:
            query_var = 'value' if self.widget in ['double slider', 'discrete slider'] else 'id'
            studies = (studies.filter(studyvariable__study_field=self.study_field,
                                      **{'studyvariable__%s__in' % query_var: selections})
                              .distinct()
                       )
        else:
            filter_on = 'id' if self.widget == 'checkbox' else 'code'
            filter_key = 'count__codes__%s__in' % filter_on
            studies = (studies.filter(count__codes__domain=self.domain,
                                      **{filter_key: selections})
                              .distinct()
                       )
        return studies

    def get_applied_filters(self, GET):
        """
        Parses passed GET url parameters to pretty string of filtering values

        Parameters:
            GET (request.GET)

        Returns:
            str
        """
        if self.widget in ['double slider', 'discrete slider']:
            from_value, to_value = GET.get(self.name).split(';')
            pretty_values = '{} - {}'.format(from_value, to_value)
        else:
            values = self.get_values()
            selections = self.get_selections(GET, values=values)
            choices = self.get_choices(values=values, include_ids=True)
            choice_dict = {str(cid): clabel for cid, ccode, clabel in choices}
            selections = [choice_dict.get(code, 'Invalid') for code in selections]
            pretty_values = ' | '.join(selections)

        return pretty_values

    def get_initial_slider_values(self, GET, **kwargs):
        """
        Get the appropriate `from_value` and `to_value` for a slider
        based on the request. Returns a dict of the form:

        dict("to_value": val, "from_value": val)

        Parameters:
            GET (request.GET)

        Returns:
            dict
        """

        selection = GET.get(self.name)
        if selection:
            if self.widget == 'discrete slider':
                labels = [v for _, v in self.get_choices(**kwargs)]
                [from_value, to_value] = list(map(lambda x: labels.index(x), selection.split(';')))
            elif self.widget == 'double slider':
                initial_values = map(float, selection.split(';'))
                [from_value, to_value] = [int(v) if v.is_integer() else v for v in initial_values]
            else:
                raise ValueError
            slider_values = dict(from_value=from_value, to_value=to_value)
        else:
            slider_values = dict()

        return slider_values

    def is_full_range(self, from_value, to_value):
        """
        Checks if the from_value and to_value are the first and last
        elements of the whole slider range

        Parameters:
            from_value (str)
            to_value (str)

        Returns:
            bool
        """

        if self.widget == 'discrete slider':
            labels = list(zip(*self.get_choices()))[1]
            return labels[0] == from_value and labels[-1] == to_value
        elif self.widget == 'double slider':
            values = self.get_values()
            return (float(values[0]) >= float(from_value) and
                    float(values[-1]) <= float(to_value))
        else:
            raise ValueError

    def __str__(self):
        return self.label


class Variable(models.Model):

    domain = models.ForeignKey(
        Domain, verbose_name='Domain',
        help_text='The broad category the condition falls under.',
        db_index=True,
    )

    category = models.CharField(
        max_length=100, null=True, verbose_name='Category',
        help_text='A specific category under the domain.')

    code = models.CharField(
        max_length=10, verbose_name='Code',
        help_text='Short identifying code to classify a condition.')

    label = models.CharField(
        max_length=100, verbose_name='Label',
        help_text='Descriptive name for the condition.')

    class Meta:
        unique_together = ('domain', 'code',)
        verbose_name_plural = "variables"

    def __str__(self):
        if self.category:
            return '{0}| {1} - {2}: {3}'.format(
                self.id, self.domain.code, self.category, self.code
            )
        else:
            return '{0}| {1}: {2}'.format(self.id, self.domain.code, self.code)


class Count(models.Model):

    count = models.IntegerField(
        help_text='Number of observations associated with the specified study and codes.')

    subjects = models.IntegerField(
        help_text='Number of subjects associated with the specified study and codes.')

    study = models.ForeignKey(
        Study, on_delete=models.CASCADE,
        help_text='The study associated with the count.',
        db_index=True,
    )

    codes = models.ManyToManyField(
        Variable,
        help_text='The codes used to classify the count.',
        db_index=True
    )

    def __str__(self):
        return '{0}: {1}'.format(self.study, self.count)
