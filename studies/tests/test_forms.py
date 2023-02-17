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

import pytest
from django.core.urlresolvers import reverse

from crispy_forms_foundation.layout.containers import (
    AccordionItem, AccordionHolder
    )
from crispy_forms.layout import HTML

from ..fields import RangeField, DiscreteRangeField, ExtendedMultipleChoiceField
from ..forms import VariableListForm, StudyFilterForm, StudyExplorerForm
from .factories import (
    DomainFactory,
    FilterFactory,
    StudyFactory,
    StudyFieldFactory,
    StudyVariableFactory,
    VariableFactory,
    )


@pytest.mark.django_db
def test_study_explorer_form_no_study_args_in_get_params(rf):
    # setup the test variables
    studies = StudyFactory.create_batch(3)

    # setup the request with no study GET parameter
    request = rf.get(reverse('study-explorer'))

    form = StudyExplorerForm(request=request)

    assert list(form.fields['study'].queryset) == studies
    assert form.initial == {'study': [-1]}


@pytest.mark.django_db
def test_study_explorer_form_with_study_args_in_get_params(rf):
    # setup the test variables
    studies = StudyFactory.create_batch(4)
    get_params = {'study': [str(studies[3].id), str(studies[2].id)]}

    # setup the request
    request = rf.get(reverse('study-explorer'), data=get_params)

    form = StudyExplorerForm(request=request)

    # should be studies in get params (sorted by id)
    # then remaining studies (sorted by id)
    expected = studies[2:] + studies[:2]

    assert list(form.fields['study'].queryset) == expected
    assert form.initial == {'study': get_params['study']}


@pytest.mark.django_db
def test_study_explorer_form_search_autocomplete_object_is_correct(rf):
    # setup test variables
    study = StudyFactory()

    # setup the request
    request = rf.get(reverse('study-explorer'))

    form = StudyExplorerForm(request=request)

    expected = [dict(label=study.study_id,
                     value=study.study_id,
                     id=1)]

    assert form.search_autocomplete_options == expected


# probably should obviate (and should be empty)
@pytest.mark.django_db
def test_study_filter_no_defined_filters(rf):
    # setup the request
    request = rf.get(reverse('study-filter'))

    form = StudyFilterForm(request=request)
    assert form.fields == {}


@pytest.mark.django_db
def test_study_filter_form_get_filter_layout_and_field_method_field_widget(rf):
    qualifier_domain = DomainFactory(is_qualifier=True, code='QUAL', label='Qualifier')
    filt = FilterFactory(domain=qualifier_domain, label='sample', study_field=None)

    request = rf.get(reverse('study-filter'))
    filter_form = StudyFilterForm(request=request)
    layout_item, form_field = filter_form._get_filter_layout_and_field(filt)

    assert layout_item.active is False
    assert layout_item.fields[0].template == 'foundation-5/field.html'
    assert layout_item.fields[0].fields == [qualifier_domain.code]
    assert isinstance(form_field, ExtendedMultipleChoiceField)
    assert not hasattr(form_field, 'pretty_initial')


@pytest.mark.django_db
def test_study_filter_form_get_filter_layout_and_field_method_domain_widget(rf):
    domain = DomainFactory(code='TEST', label='Test label')
    domain_filter = FilterFactory(domain=domain, label='Test label', study_field=None)

    request = rf.get(reverse('study-filter'))
    filter_form = StudyFilterForm(request=request)
    layout_item, form_field = filter_form._get_filter_layout_and_field(domain_filter)

    assert layout_item.active is False
    assert layout_item.fields[0].template == 'forms/domain-widget.html'
    assert layout_item.fields[0].fields == [domain.code]
    assert isinstance(form_field, ExtendedMultipleChoiceField)
    assert not hasattr(form_field, 'pretty_initial')


@pytest.mark.django_db
def test_study_filter_form_get_filter_layout_and_field_method_discrete_slider_widget(rf):
    domain = DomainFactory(code="bat")
    VariableFactory(code='FOO', label="foo", domain=domain)
    VariableFactory(code='BAR', label="bar", domain=domain)
    study_filter = FilterFactory(domain=domain, widget='discrete slider', study_field=None)

    request = rf.get(reverse('study-filter'))
    filter_form = StudyFilterForm(request=request)
    layout_item, form_field = filter_form._get_filter_layout_and_field(study_filter)

    assert layout_item.active is False
    assert layout_item.fields[0].template == 'forms/range-widget.html'
    assert layout_item.fields[0].fields == [domain.code]
    assert isinstance(form_field, DiscreteRangeField)
    assert not hasattr(form_field, 'pretty_initial')


@pytest.mark.django_db
def test_study_filter_form_get_filter_layout_and_field_method_double_slider_widget(rf):
    field = StudyFieldFactory(field_name='START_YEAR')

    StudyVariableFactory(study_field=field, value=1998)
    StudyVariableFactory(study_field=field, value=2000)

    study_filter = FilterFactory(study_field=field, domain=None, widget='double slider')

    request = rf.get(reverse('study-filter'))
    filter_form = StudyFilterForm(request=request)

    layout_item, form_field = filter_form._get_filter_layout_and_field(study_filter)

    assert layout_item.active is False
    assert layout_item.fields[0].template == 'forms/range-widget.html'
    assert layout_item.fields[0].fields == ['START_YEAR']
    assert isinstance(form_field, RangeField)
    assert not hasattr(form_field, 'pretty_initial')


@pytest.mark.django_db
def test_study_filter_form_get_filter_layout_and_field_method_checkbox_with_initial_values(rf):
    qualifier_domain = DomainFactory(is_qualifier=True, code='QUAL', label='Qualifier')
    qual_filter = FilterFactory(domain=qualifier_domain, label='sample', study_field=None)
    var1 = VariableFactory(code='0', label="FOO", domain=qualifier_domain)
    var2 = VariableFactory(code='1', label="BAR", domain=qualifier_domain)

    get_params = {"QUAL": [var1.id, var2.id]}

    request = rf.get(reverse('study-filter'), data=get_params)
    filter_form = StudyFilterForm(request=request)
    layout_item, form_field = filter_form._get_filter_layout_and_field(qual_filter)

    assert layout_item.active is True
    assert form_field.pretty_initial == "FOO | BAR"


@pytest.mark.django_db
def test_study_filter_form_get_filter_layout_and_field_method_slider_with_initial_values(rf):
    field = StudyFieldFactory(field_name='START_YEAR')

    StudyVariableFactory(study_field=field, value=1998)
    StudyVariableFactory(study_field=field, value=2000)
    study_filter = FilterFactory(study_field=field, domain=None, widget='double slider')

    get_params = {"START_YEAR": "1998;2000"}

    request = rf.get(reverse('study-filter'), data=get_params)
    filter_form = StudyFilterForm(request=request)

    layout_item, form_field = filter_form._get_filter_layout_and_field(study_filter)

    assert layout_item.active is True
    assert form_field.pretty_initial == "1998 - 2000"


@pytest.mark.django_db
def test_study_filter_form_get_filter_layout_and_field_method_discrete_slider_with_initial_values(rf):
    domain = DomainFactory(code="DOMAIN", is_qualifier=True)
    VariableFactory(domain=domain, code='0', label="A")
    VariableFactory(domain=domain, code='1', label="B")
    VariableFactory(domain=domain, code='2', label="C")
    VariableFactory(domain=domain, code='3', label="D")

    filt = FilterFactory(domain=domain, study_field=None, widget='discrete slider')

    get_params = {"DOMAIN": "A;C"}

    request = rf.get(reverse('study-filter'), data=get_params)
    filter_form = StudyFilterForm(request=request)

    layout_item, form_field = filter_form._get_filter_layout_and_field(filt)

    assert layout_item.active is True
    assert form_field.pretty_initial == "A - C"


@pytest.mark.django_db
def test_study_filter_get_accordion_or_empty_method_no_filter(rf):
    request = rf.get(reverse('study-filter'))
    filter_form = StudyFilterForm(request=request)

    items = []

    layout = filter_form._get_accordion_or_empty(items)

    assert isinstance(layout, HTML)


@pytest.mark.django_db
def test_study_filter_get_accordion_or_empty_method_no_items_kwarg(rf):
    request = rf.get(reverse('study-filter'))
    filter_form = StudyFilterForm(request=request)

    items = []

    layout = filter_form._get_accordion_or_empty(items)

    assert isinstance(layout, HTML)


@pytest.mark.django_db
def test_study_filter_get_accordion_or_empty_method_with_items_kwargs(rf):
    request = rf.get(reverse('study-filter'))
    filter_form = StudyFilterForm(request=request)

    items = [AccordionItem("foo"), AccordionItem("bar")]

    layout = filter_form._get_accordion_or_empty(items)

    assert isinstance(layout, AccordionHolder)


@pytest.mark.django_db
def test_variable_list_form_category_field_is_disabled_for_domain_without_categories_fields_in_variables(rf):
    # setup domain and request
    domain = DomainFactory()
    request = rf.get(reverse('variable-list', kwargs={"domain_code": domain.code}))

    # create domain variables to without category field
    VariableFactory(domain=domain)
    VariableFactory(domain=domain)

    form = VariableListForm(request=request, domain=domain)

    # assert category form field for qualifier domain is disabled and has only default choice
    assert form.fields['category'].disabled is True
    assert form.fields['category'].choices == [(None, 'Search by Category')]


@pytest.mark.django_db
def test_variable_list_form_category_field_is_not_disabled_for_domain_with_categories_fields_in_variables(rf):
    # setup domain and requestt
    domain = DomainFactory(is_qualifier=False)
    request = rf.get(reverse('variable-list', kwargs={"domain_code": domain.code}))

    # create domain variables and populate category field
    VariableFactory(domain=domain, category="B")
    VariableFactory(domain=domain, category="A")

    form = VariableListForm(request=request, domain=domain)

    # assert category form field is not disabled and has default + variable categories (in sorted order)
    assert form.fields['category'].disabled is False
    assert form.fields['category'].choices == [(None, 'Search by Category'), ("A", "A"), ("B", "B")]


@pytest.mark.django_db
def test_variable_list_form_has_correct_initial_values(rf):
    get_params = dict(category="A", variable="foo")

    # setup domain and request with initial_data as GET parameters
    domain = DomainFactory(is_qualifier=True)
    request = rf.get(reverse('variable-list', kwargs={"domain_code": domain.code}), data=get_params)

    form = VariableListForm(request=request, domain=domain)

    assert form.initial == get_params


@pytest.mark.django_db
def test_variable_list_form_variable_autocomplete_attribute(rf):
    # setup domain and request with initial_data as GET parameters
    domain = DomainFactory()
    request = rf.get(reverse('variable-list', kwargs={"domain_code": domain.code}))

    # create domain variables to populate variable field _autocomplete
    VariableFactory(domain=domain, code="A", label="foo")
    VariableFactory(domain=domain, code="B", label="bar")

    form = VariableListForm(request=request, domain=domain)

    assert form.variable_autocomplete_options == ["A", "B", "bar", "foo"]
