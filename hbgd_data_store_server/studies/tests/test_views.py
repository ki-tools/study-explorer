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

from unittest import mock
import pytest
import pandas as pd

from django.core.urlresolvers import reverse
from django.http import Http404

from ..forms import StudyExplorerForm

from ..views import (
    StudyListView,
    VariableListView,
    StudyFilterView,
    StudyExplorerView,
)

from .factories import (
    AgeDomainFactory,
    AgeVariableFactory,
    CountFactory,
    DomainFactory,
    FilterFactory,
    SampleVariableFactory,
    SampleDomainFactory,
    StudyFactory,
    StudyFieldFactory,
    StudyVariableFactory,
    VariableFactory,
)

nan = pd.np.nan


# Test components of views
def _get_instance(cls, initkwargs=None, request=None, *args, **kwargs):
    """
    Returns a decorated instance of a class-based generic view class.
    Use `initkwargs` to set expected class attributes.
    For example, set the `object` attribute on MyDetailView class:
        instance = _get_instance(MyDetailView, initkwargs={'object': obj}, request)
    because SingleObjectMixin (part of generic.DetailView)
    expects self.object to be set before invoking get_context_data().
    `args` and `kwargs` are the same values you would pass to ``reverse()``.
    """
    if initkwargs is None:
        initkwargs = {}
    instance = cls(**initkwargs)
    instance.request = request
    instance.args = args
    instance.kwargs = kwargs
    return instance


@pytest.mark.parametrize("big_order, field_type, table_data", [
    (9, 'str', [{'start year': '1997.0', 'study_id': 'HIG7'}]),
    (-1, 'str', [{'stop year': '1999.0', 'start year': '1997.0', 'study_id': 'HIG7'}]),
    (-1, 'int', [{'stop year': '1999.0', 'start year': 1997, 'study_id': 'HIG7'}]),
    (-1, 'float', [{'stop year': '1999.0', 'start year': 1997.0, 'study_id': 'HIG7'}]),
])
@pytest.mark.django_db
def test_study_list_view_get_study_dict_big_order_field_type_returns(rf, big_order, field_type, table_data):
    StudyFieldFactory(field_name='start_year', label='start year',
                      big_order=big_order, field_type=field_type)
    StudyFieldFactory(field_name='stop_year', label='stop year')
    study = StudyFactory(study_id='HIG7')
    StudyVariableFactory(study_field__field_name='start_year',
                         studies=[study], value='1997.0')
    StudyVariableFactory(study_field__field_name='stop_year',
                         studies=[study], value='1999.0')

    request = rf.get(reverse('study-list'))
    study_list_view = _get_instance(StudyListView, request=request)
    assert study_list_view.get_study_dict() == table_data


@pytest.mark.django_db
def test_study_list_view_table_fields_reflect_changes(rf):
    start_year = StudyFieldFactory(label='start_year')
    stop_year = StudyFieldFactory(label='stop_year')
    StudyVariableFactory(study_field=start_year)
    StudyVariableFactory(study_field=stop_year)

    request = rf.get(reverse('study-list'))
    study_list_view = _get_instance(StudyListView, request=request)
    table_data = study_list_view.get_study_dict()
    study_list_view = _get_instance(StudyListView, {'table_data': table_data}, request=request)
    table = study_list_view.get_table()
    assert table.sequence == ['study_id', 'start_year', 'stop_year']

    start_year.big_order = 9
    start_year.save()
    table = study_list_view.get_table()
    assert table.sequence == ['study_id', 'start_year']

    stop_year.big_order = 1
    stop_year.save()
    table = study_list_view.get_table()
    assert table.sequence == ['study_id', 'stop_year', 'start_year']

    start_year.big_order = -1
    start_year.save()
    table = study_list_view.get_table()
    assert table.sequence == ['study_id', 'stop_year']


@pytest.mark.django_db
def test_study_list_view_table_deleted_fields_disappear_from_table_if_no_order_defined(rf):
    start_year = StudyFieldFactory(label='start_year')
    stop_year = StudyFieldFactory(label='stop_year')
    StudyVariableFactory(study_field=start_year)
    StudyVariableFactory(study_field=stop_year)

    stop_year.delete()
    request = rf.get(reverse('study-list'))
    study_list_view = _get_instance(StudyListView, request=request)
    table_data = study_list_view.get_study_dict()
    study_list_view = _get_instance(StudyListView, {'table_data': table_data}, request=request)
    table = study_list_view.get_table()
    assert table.sequence == ['study_id', 'start_year']


@pytest.mark.django_db
def test_study_list_view_table_deleted_fields_disappear_from_table_if_order_defined(rf):
    start_year = StudyFieldFactory(label='start_year', big_order=10)
    stop_year = StudyFieldFactory(label='stop_year', big_order=3)
    StudyVariableFactory(study_field=start_year)
    StudyVariableFactory(study_field=stop_year)

    stop_year.delete()
    request = rf.get(reverse('study-list'))
    study_list_view = _get_instance(StudyListView, request=request)
    table_data = study_list_view.get_study_dict()
    study_list_view = _get_instance(StudyListView, {'table_data': table_data}, request=request)
    table = study_list_view.get_table()
    assert table.sequence == ['study_id', 'start_year']


@pytest.mark.django_db
def test_variable_list_view_get_method_sets_domain_attribute(rf):
    # setup test variable
    variable = SampleVariableFactory()

    # setup view
    request = rf.get(reverse('variable-list', kwargs={"domain_code": variable.domain.code}))
    variable_list_view = _get_instance(VariableListView, request=request)

    variable_list_view.get(request, domain_code=variable.domain.code)
    assert hasattr(variable_list_view, 'domain')


@pytest.mark.django_db
def test_variable_list_view_get_queryset_no_category_or_variable_filters(rf):
    # setup test variables
    variables = SampleVariableFactory.create_batch(2)
    domain = variables[0].domain

    # setup view
    request = rf.get(reverse('variable-list', kwargs={"domain_code": domain.code}))
    variable_list_view = _get_instance(VariableListView, {'domain': domain}, request=request)

    queryset = variable_list_view.get_queryset().order_by('id')
    assert list(queryset) == list(variables)


@pytest.mark.django_db
def test_variable_list_view_redirect_if_reset_in_querydict(rf):
    # setup test variables
    domain = SampleDomainFactory()
    kwargs = {"domain_code": domain.code}
    # setup the view
    url = reverse('variable-list', kwargs=kwargs)
    request = rf.get(url, data={"Reset": "Clear Filters"})
    variable_list_view = _get_instance(VariableListView, request=request)

    response = variable_list_view.get(request, **kwargs)
    assert response.status_code == 302
    assert response.url == '/studies/variables/SAMPLE'


@pytest.mark.django_db
def test_variable_list_view_dont_redirect_if_reset_not_in_querydict(rf):
    # setup test variables
    domain = SampleDomainFactory()
    kwargs = {"domain_code": domain.code}

    # setup the view
    request = rf.get(reverse('variable-list', kwargs={"domain_code": domain.code}))
    variable_list_view = _get_instance(VariableListView, request=request)

    response = variable_list_view.get(request, **kwargs)
    assert response.status_code == 200


@pytest.mark.django_db
def test_variable_list_view_get_queryset_with_category_filter_on_category(rf):
    # setup test variables
    domain = SampleDomainFactory()
    variable_A = SampleVariableFactory(domain=domain, category="A")
    SampleVariableFactory(domain=domain, category="B")

    # setup view with filter on category="A"
    request = rf.get(reverse('variable-list', kwargs={"domain_code": domain.code}), data={"category": "A"})
    variable_list_view = _get_instance(VariableListView, {'domain': domain}, request=request)

    queryset = variable_list_view.get_queryset().order_by('id')
    assert list(queryset) == [variable_A]


@pytest.mark.django_db
def test_variable_list_view_get_queryset_with_variable_filter_on_label(rf):
    # set-up domain and url
    domain = SampleDomainFactory()
    url = reverse('variable-list', kwargs={"domain_code": domain.code})

    # setup multiple variables so we can test filtering
    variable_1 = SampleVariableFactory(label="Alpha-Carotene", domain=domain)
    SampleVariableFactory(label="Beta-Carotene", domain=domain)

    # setup view
    request = rf.get(url, data={"variable": variable_1.label})
    variable_list_view = _get_instance(VariableListView, {'domain': domain}, request=request)

    # get queryset
    expected_queryset = list(variable_list_view.get_queryset())
    assert expected_queryset == [variable_1]


@pytest.mark.django_db
def test_variable_list_view_get_queryset_with_variable_filter_on_code(rf):
    # set-up domain and url
    domain = SampleDomainFactory()
    url = reverse('variable-list', kwargs={"domain_code": domain.code})

    # setup multiple variables so we can test filtering
    variable_1 = SampleVariableFactory(code="ACARO", domain=domain)
    SampleVariableFactory(code="BCARO", domain=domain)

    # setup view
    request = rf.get(url, data={"variable": variable_1.code})
    variable_list_view = _get_instance(VariableListView, {'domain': domain}, request=request)

    # get queryset
    expected_queryset = list(variable_list_view.get_queryset())
    assert expected_queryset == [variable_1]


@pytest.mark.django_db
def test_variable_list_view_get_context_data_domains_by_is_qualifier_bool(rf):
    domain_1 = SampleDomainFactory(code="A", is_qualifier=False)
    domain_2 = SampleDomainFactory(code="B", is_qualifier=True)

    request = rf.get(reverse('variable-list', kwargs={"domain_code": domain_1.code}))
    variable_list_view = _get_instance(VariableListView, {'domain': domain_1}, request=request)

    variable_list_view.object_list = variable_list_view.get_queryset()
    context = variable_list_view.get_context_data()

    assert list(context['domains']) == [domain_1]
    assert list(context['qualifiers']) == [domain_2]
    # domain_1 is the active domain
    assert context['domain'].id == domain_1.id


@pytest.mark.django_db
def test_variable_list_view_get_context_data_table_fields_hide_category_if_no_category_in_queryset(rf):
    # setup test variables
    variable_1 = SampleVariableFactory()

    # setup view
    request = rf.get(reverse('variable-list', kwargs={"domain_code": variable_1.domain.code}))
    variable_list_view = _get_instance(VariableListView, {'domain': variable_1.domain}, request=request)

    # Have to manually set `object_list` attr that is normally set by `get` method
    variable_list_view.object_list = variable_list_view.get_queryset()

    context = variable_list_view.get_context_data()
    assert context['table'].exclude == ('category',)


@pytest.mark.django_db
def test_study_explorer_view_redirect_if_reset_in_querydict(rf):
    # setup the view
    request = rf.get(reverse('study-explorer'), data={"Reset": "Clear Filters"})
    study_explorer_view = _get_instance(StudyExplorerView, request=request)

    response = study_explorer_view.get(request)
    assert response.status_code == 302
    assert response.url == '/studies/explorer'


@pytest.mark.django_db
def test_study_explorer_view_mixed_study_filters_and_study_ids(rf):
    # setup the view
    request = rf.get(reverse('study-explorer'), data={"study": 0, 'RELTIVE': 0})
    study_explorer_view = _get_instance(StudyExplorerView, request=request)

    with pytest.raises(Http404):
        study_explorer_view.get(request)


@pytest.mark.django_db
def test_study_explorer_view_dont_redirect_if_reset_not_in_querydict(rf):
    # setup the view
    request = rf.get(reverse('study-explorer'))
    study_explorer_view = _get_instance(StudyExplorerView, request=request)

    response = study_explorer_view.get(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_study_explorer_get_context_data_no_get_parameters(rf):
    # setup the view
    request = rf.get(reverse('study-explorer'))
    study_explorer_view = _get_instance(StudyExplorerView, request=request)

    context = study_explorer_view.get_context_data()
    assert context.get('domains') is None
    assert isinstance(context['form'], StudyExplorerForm)


@pytest.mark.django_db
def test_study_explorer_get_context_with_study_get_params(rf):
    # setup test variables
    domain = SampleDomainFactory(code="AGECAT")
    study = StudyFactory(study_id="foo")
    variable = SampleVariableFactory(label="bar", domain=domain, code=1)
    CountFactory(codes=[variable], study=study, count=10)

    # setup view
    request = rf.get(reverse('study-explorer'), data={"study": [study.id]})
    study_explorer_view = _get_instance(StudyExplorerView, request=request)

    context = study_explorer_view.get_context_data()

    domain_acc = context['domains'][0]
    assert domain_acc['label'] == domain.label
    assert domain_acc['code'] == domain.code
    assert domain_acc['count'] == 10


@pytest.mark.django_db
def test_study_export_view_given_domain_data_returns_values(client):
    age_domain = SampleDomainFactory(code="AGECAT")
    data_domain = SampleDomainFactory()
    study = StudyFactory(study_id="foo")
    age_variable = SampleVariableFactory(label="bar", domain=age_domain, code=1)
    data_variable = SampleVariableFactory(label="bat", domain=data_domain, code=2)
    CountFactory(codes=[age_variable, data_variable], study=study, count=10)

    response = client.get(reverse('export', kwargs={"domain_id": data_domain.id}), {'start_year': '1996;2000'}, follow=True)
    assert response.status_code == 200


@pytest.mark.django_db
def test_study_export_by_age_view_given_domain_data_returns_values(client):
    age_domain = SampleDomainFactory(code="AGECAT")
    data_domain = SampleDomainFactory()
    study = StudyFactory(study_id="foo")
    age_variable = SampleVariableFactory(label="bar", domain=age_domain, code=1)
    data_variable = SampleVariableFactory(label="bat", domain=data_domain, code=2)
    CountFactory(codes=[age_variable, data_variable], study=study, count=10)

    response = client.get(reverse('export_by_age', kwargs={"domain_id": data_domain.id}), {'start_year': '1996;2000'}, follow=True)
    assert response.status_code == 200


@pytest.mark.django_db
def test_study_filter_view_get_method_filter_reset_get_param_and_redirect(rf):
    # setup the view
    request = rf.get(reverse('study-filter'), data={"Reset": "Clear Filters"})
    study_filter_view = _get_instance(StudyFilterView, request=request)

    response = study_filter_view.get(request)
    assert response.status_code == 302
    assert response.url == '/studies/filter'


@pytest.mark.django_db
def test_study_filter_view_get_method_filter_empty_GET_params_and_redirect(rf):
    # setup the view
    request = rf.get(reverse('study-filter'), data={'foo': ["", ""], 'bar': "", 'bat': "10"})
    study_filter_view = _get_instance(StudyFilterView, request=request)

    response = study_filter_view.get(request)
    assert response.status_code == 302
    assert response.url == '/studies/filter?bat=10'


@pytest.mark.django_db
def test_study_filter_view_get_method_filter_renders(client):
    field = StudyFieldFactory(field_name='start_year')

    StudyVariableFactory(study_field=field, value='1996')
    StudyVariableFactory(study_field=field, value='2000')

    FilterFactory(study_field=field, domain=None, widget='double slider')

    response = client.get(reverse('study-filter'), {'start_year': '1996;2000'}, follow=True)
    assert response.status_code == 200


@pytest.mark.django_db
def test_study_filter_view_get_method_filter_apply_GET_param_and_redirect(client):
    response = client.get(reverse('study-filter'), {'Apply': 'Apply'}, follow=True)
    last_url, status_code = response.redirect_chain[-1]
    assert status_code == 302
    assert last_url == '/studies/filter'


@pytest.mark.django_db
def test_study_filter_view_renders_without_filters(client):
    "Ensure the study filter view renders without any filters defined"
    response = client.get(reverse('study-filter'))
    assert response.status_code == 200


def _set_up_study_filter_view(rf, data=None):
    field = StudyFieldFactory(field_name='start_year')
    request = rf.get(reverse('study-filter'), data=data)
    FilterFactory(study_field=field, domain=None)
    study_filter_view = _get_instance(StudyFilterView, request=request)
    study_filter_view.object_list = study_filter_view.get_queryset()
    return study_filter_view


@pytest.mark.django_db
def test_study_filter_view_get_context_data_sets_n_total_studies_attr(rf):
    StudyFactory.create_batch(3)
    study_filter_view = _set_up_study_filter_view(rf)
    context = study_filter_view.get_context_data()
    assert context['n_total'] == 3


@pytest.mark.django_db
def test_study_filter_view_get_context_GET_params_for_multiple_values_set_on_study_field(rf):
    field = StudyFieldFactory(field_name='study_type')
    FilterFactory(study_field=field, domain=None)
    studies1 = StudyFactory.create_batch(3)
    var1 = StudyVariableFactory(studies=studies1, study_field=field, value="B")
    studies2 = StudyFactory.create_batch(3)
    var2 = StudyVariableFactory(studies=studies2, study_field=field, value="A")
    study_ids = [study.study_id for study in studies1 + studies2]
    study_filter_view = _set_up_study_filter_view(rf, data={'study_type': [var1.id, var2.id]})
    context = study_filter_view.get_context_data()
    assert list(context['filtered_studies']) == sorted(study_ids)
    assert sorted(context['GET_params'].split('&')) == sorted(['study_type=%d' % var1.id, 'study_type=%d' % var2.id])


@pytest.mark.django_db
def test_study_filter_view_get_context_data_sets_study_dict_and_field_names_to_None(rf):
    field = StudyFieldFactory(field_name='study_type')
    FilterFactory(study_field=field, domain=None)
    studies1 = StudyFactory.create_batch(3)
    var1 = StudyVariableFactory(studies=studies1, study_field=field, value="B")
    studies2 = StudyFactory.create_batch(3)
    StudyVariableFactory(studies=studies2, study_field=field, value="A")
    study_ids = [study.study_id for study in studies1]
    study_filter_view = _set_up_study_filter_view(rf, data={'study_type': var1.id})
    context = study_filter_view.get_context_data()
    assert list(context['filtered_studies']) == sorted(study_ids)
    assert context['study_dict'] is None
    assert context['field_names'] is None


@pytest.mark.django_db
def test_study_filter_view_get_context_data_sets_study_dict_and_field_names(rf):
    field = StudyFieldFactory(field_name='study_type', lil_order=0, label='TYPE')
    FilterFactory(study_field=field, domain=None)

    studies1 = StudyFactory.create_batch(3)
    var1 = StudyVariableFactory(studies=studies1, study_field=field, value="B")
    studies2 = StudyFactory.create_batch(3)
    StudyVariableFactory(studies=studies2, study_field=field, value="A")

    study_ids = sorted([study.study_id for study in studies1])
    study_filter_view = _set_up_study_filter_view(rf, data={'study_type': var1.id})
    context = study_filter_view.get_context_data()
    assert context['study_dict'] == {study_id: {'TYPE': "B"} for study_id in study_ids}
    assert list(context['field_names']) == ['TYPE']


@pytest.mark.django_db
def test_study_filter_view_get_context_data_when_no_objects_in_object_list(rf):
    field = StudyFieldFactory(field_name='study_type', lil_order=-1, label='TYPE')
    StudyFieldFactory(field_name='foo', lil_order=0, label='FOO')
    FilterFactory(study_field__field_name='foo', domain=None)

    StudyVariableFactory(studies=StudyFactory.create_batch(3),
                         study_field=field, value="B")

    study_filter_view = _set_up_study_filter_view(rf, data={'foo': '7'})
    context = study_filter_view.get_context_data()

    assert context['filtered_studies'].count() == 0


@pytest.mark.django_db
def test_study_filter_view_get_context_data_with_none_of_display_field_in_study_variables(rf):
    field = StudyFieldFactory(field_name='study_type', lil_order=-1, label='TYPE')
    StudyFieldFactory(field_name='foo', lil_order=0, label='FOO')
    FilterFactory(study_field=field, domain=None)

    var1 = StudyVariableFactory(studies=StudyFactory.create_batch(3),
                                study_field=field, value="B")
    StudyVariableFactory(studies=StudyFactory.create_batch(3),
                         study_field__field_name='foo', value="B")

    study_filter_view = _set_up_study_filter_view(rf, data={'study_type': var1.id})
    context = study_filter_view.get_context_data()

    assert context['study_dict'] is None
    assert context['field_names'] is None


@pytest.mark.django_db
def test_study_filter_view_drop_full_range_widget_GET_request(client):
    field = StudyFieldFactory(field_name='start_year')

    StudyVariableFactory(study_field=field, value='1996')
    StudyVariableFactory(study_field=field, value='2000')

    FilterFactory(study_field=field, domain=None, widget='double slider')

    response = client.get(reverse('study-filter'), {'start_year': '1996;2000'}, follow=True)
    last_url, status_code = response.redirect_chain[-1]
    assert status_code == 302
    assert last_url == '/studies/filter'


@pytest.mark.django_db
def test_explorer_view_get_context_data_adds_n_studies_and_total_studies(rf):
    study_1 = StudyFactory()
    StudyFactory()

    request = rf.get(reverse('study-explorer'), data={'study': study_1.id})
    view = _get_instance(StudyExplorerView, request=request)
    context = view.get_context_data()

    assert context['n_selected'] == 1
    assert context['n_total'] == 2


@pytest.mark.django_db
def test_explorer_view_returns_no_domains_if_no_counts(rf):
    study = StudyFactory()

    request = rf.get(reverse('study-explorer'), data={'study': study.id})
    view = _get_instance(StudyExplorerView, request=request)
    context = view.get_context_data()

    assert 'domains' not in context.keys()


@pytest.mark.django_db
def test_study_explorer_view_resolves_studies(rf):
    studies = StudyFactory.create_batch(7)
    StudyVariableFactory(studies=studies[:5],
                         study_field__field_name='study_type',
                         value='strawberry')
    StudyVariableFactory(studies=[studies[5]],
                         study_field__field_name='study_type',
                         value='vanilla')
    var1 = StudyVariableFactory(studies=[studies[6]],
                                study_field__field_name='study_type',
                                value='chocolate')
    FilterFactory(study_field__field_name='study_type', domain=None, label='HAHA')

    request = rf.get(reverse('study-explorer'), data={'study_type': [var1.id]})
    view = _get_instance(StudyExplorerView, request=request)
    view.get_context_data()

    assert [studies[6].id] == request.GET.getlist('study')


@pytest.mark.django_db
def test_study_explorer_view_sets_applied_filters(rf):
    studies = StudyFactory.create_batch(7)
    StudyVariableFactory(studies=studies[:5],
                         study_field__field_name='study_type',
                         value='strawberry')
    var1 = StudyVariableFactory(studies=[studies[5]],
                                study_field__field_name='study_type',
                                value='vanilla')
    var2 = StudyVariableFactory(studies=[studies[6]],
                                study_field__field_name='study_type',
                                value='chocolate')
    FilterFactory(study_field__field_name='study_type', domain=None, label='HAHA')

    request = rf.get(reverse('study-explorer'), data={'study_type': [var2.id, var1.id]})
    view = _get_instance(StudyExplorerView, request=request)
    context = view.get_context_data()

    assert context['applied_filters'] == [('HAHA', 'chocolate | vanilla')]


@mock.patch('bokeh.embed.components')
@pytest.mark.django_db
def tests_explorer_view_get_context_data_adds_domains_properties_correctly(mock_components, rf):  # noqa
    # Should be n_items for n_domains
    # Should alphabetically order domains
    # Should have sum of counts by domain populated by get_domain_counts method
    # Should have domain label and domain code
    # Should be in alphabetical order

    study = StudyFactory()
    d_c = DomainFactory(label='c')
    d_a = DomainFactory(label='a')
    d_b = DomainFactory(label='b')
    age_domain = AgeDomainFactory(label='d')
    var_a = VariableFactory(domain=d_a)
    var_b = VariableFactory(domain=d_b)
    var_c = VariableFactory(domain=d_c)
    age_var = AgeVariableFactory(domain=age_domain)
    CountFactory(codes=[age_var, var_a], study=study, count=100)
    CountFactory(codes=[age_var, var_b], study=study, count=100)
    CountFactory(codes=[age_var, var_c], study=study, count=100)

    request = rf.get(reverse('study-explorer'), data={'study': study.id})
    view = _get_instance(StudyExplorerView, request=request)

    # Set mock get_domain_count return value
    mock_components.return_value = ('script', {
        d_a.label: 'div_a', d_b.label: 'div_b', d_c.label: 'div_c'
    })
    context = view.get_context_data()

    context_domains = context['domains']
    assert len(context_domains) == 4
    for i, domain in enumerate([d_a, d_b, d_c, age_domain]):
        print(domain.label)
        assert context_domains[i]['label'] == domain.label
        assert context_domains[i]['code'] == domain.code.strip('*')
        assert context_domains[i]['id'] == domain.id
        if i == 3:  # Handle age domain separately
            count = 300
        else:
            assert context_domains[i]['heatmap'] == 'div_%s' % domain.label.strip('*')
            count = 100
        assert context_domains[i]['count'] == count

    context_age_domains = context['age_domains']
    assert len(context_age_domains) == 3
    for i, domain in enumerate([d_a, d_b, d_c]):
        assert context_age_domains[i]['label'] == domain.label
        assert context_age_domains[i]['code'] == domain.code.strip('*')
        assert context_age_domains[i]['id'] == domain.id
        assert context_age_domains[i]['age_heatmap'] == 'div_%s' % domain.label.strip('*')
        assert context_age_domains[i]['count'] == 100
    # Check scripts
    assert context['plot_summary_script'] == 'script'
    assert context['plot_script'] == 'script'
    assert context['plot_age_script'] == 'script'
    # Note: not testing plot_summary_div as blanket means it doesn't really make sense
