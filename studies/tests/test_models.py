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
from django.db.utils import IntegrityError
from django.forms import ValidationError

from ..models import (
    StudyField,
    Study,
    StudyVariable,
    Filter,
)

from .factories import (
    StudyFieldFactory,
    StudyFactory,
    StudyVariableFactory,
    SampleVariableFactory as VariableFactory,
    CountFactory,
    DomainFactory,
    FilterFactory
)


@pytest.mark.django_db
def test_study_field_str_repr_returns_label():
    study_field = StudyFieldFactory(label='STOP YEAR')
    assert str(study_field) == 'STOP YEAR'


@pytest.mark.django_db
def test_study_field_str_repr_returns_field_name_with_underscore_replaced_by_spaces():
    study_field = StudyFieldFactory(field_name='PI_in_charge')
    assert str(study_field) == 'Pi In Charge'


@pytest.mark.django_db
def test_study_field_str_repr_returns_field_name_with_titleized():
    study_field = StudyFieldFactory(field_name='PI in charge')
    assert str(study_field) == 'Pi In Charge'


@pytest.mark.django_db
def test_study_field_nonunique_field_name_creates_clash():
    StudyFieldFactory(field_name='stop_year')
    with pytest.raises(IntegrityError):
        StudyFieldFactory(field_name='stop_year')


@pytest.mark.django_db
def test_study_field_field_type_as_list_passes_if_variables_empty():
    assert StudyFieldFactory(field_type='list').field_type == 'list'


@pytest.mark.django_db
def test_study_field_field_type_as_list_passes_if_at_least_one_preexisting_variable_contains_seperator():
    study_field = StudyFieldFactory()
    StudyVariableFactory(study_field=study_field, value='cat')
    StudyVariableFactory(study_field=study_field, value='cat, dog')
    study_field.field_type = 'list'
    study_field.clean()
    assert study_field.field_type == 'list'


@pytest.mark.django_db
def test_study_field_field_type_int_passes_if_variables_empty():
    assert StudyFieldFactory(field_type='int').field_type == 'int'


@pytest.mark.django_db
def test_study_field_field_type_int_passes_if_all_preexisting_variables_castable_as_int():
    study_field = StudyFieldFactory()
    StudyVariableFactory(study_field=study_field, value='1.0')
    StudyVariableFactory(study_field=study_field, value='3')
    study_field.field_type = 'int'
    study_field.save()
    assert study_field.field_type == 'int'


@pytest.mark.django_db
def test_study_field_field_type_int_clean_raises_error_if_any_preexisting_variables_not_castable_as_int():
    study_field = StudyFieldFactory()
    StudyVariableFactory(study_field=study_field, value='13')
    StudyVariableFactory(study_field=study_field, value='13.2')
    study_field.field_type = 'int'
    with pytest.raises(ValidationError):
        study_field.clean()


@pytest.mark.django_db
def test_study_field_field_type_float_passes_if_variables_empty():
    assert StudyFieldFactory(field_type='float').field_type == 'float'


@pytest.mark.django_db
def test_study_field_field_type_int_passes_if_all_preexisting_variables_castable_as_float():
    study_field = StudyFieldFactory()
    StudyVariableFactory(study_field=study_field, value='1')
    StudyVariableFactory(study_field=study_field, value='-3.2')
    study_field.field_type = 'float'
    study_field.save()
    assert study_field.field_type == 'float'


@pytest.mark.django_db
def test_study_field_field_type_float_clean_raises_error_if_any_preexisting_variable_not_castable_as_float():
    study_field = StudyFieldFactory()
    StudyVariableFactory(study_field=study_field, value='12.3')
    StudyVariableFactory(study_field=study_field, value='cat')
    study_field.field_type = 'float'
    with pytest.raises(ValidationError):
        study_field.clean()


@pytest.mark.django_db
def test_study_field_get_values_returns_empty_list_if_no_variables_present():
    assert StudyFieldFactory().get_values() == []


@pytest.mark.django_db
def test_study_field_get_values_returns_distinct_variables_if_not_in_EMPTY_IDENTIFIERS():
    field = StudyFieldFactory()
    StudyVariableFactory()
    StudyVariableFactory(study_field=field, value='donkey')
    StudyVariableFactory(study_field=field, value='13')
    StudyVariableFactory(study_field=field, value='None')
    assert field.get_values() == sorted(['donkey', '13'])


@pytest.mark.django_db
def test_study_str_repr_returns_study_id():
    study = StudyFactory(study_id='test_id')
    assert str(study) == 'test_id'


@pytest.mark.django_db
def test_study_nonunique_study_id_creates_clash():
    StudyFactory(study_id='test_id')
    with pytest.raises(IntegrityError):
        StudyFactory(study_id='test_id')


# STUDY VARIABLE
@pytest.mark.django_db
def test_study_variable_str_repr_returns_study_field_label_value():
    study_variable = StudyVariableFactory(study_field__label='START YEAR',
                                          value='1994.0')
    assert str(study_variable) == 'START YEAR: 1994.0'


@pytest.mark.django_db
def test_study_variable_nonunique_value_and_study_field_creates_clash():
    StudyVariableFactory(study_field__field_name='stop_year',
                         value='1994.0')
    with pytest.raises(IntegrityError):
        StudyVariableFactory(study_field__field_name='stop_year',
                             value='1994.0')


@pytest.mark.django_db
def test_study_variable_clean_field_type_list_always_passes():
    StudyVariableFactory(study_field__field_type='list', value='10').clean()


@pytest.mark.django_db
def test_study_variable_clean_field_type_float_passes_if_value_castable_to_float():
    StudyVariableFactory(study_field__field_type='float', value='12.3').clean()


@pytest.mark.django_db
def test_study_variable_clean_field_type_float_raises_error_if_value_not_castable_to_float():
    with pytest.raises(ValidationError):
        assert StudyVariableFactory(study_field__field_type='float', value='cat').clean()


@pytest.mark.django_db
def test_study_variable_clean_field_type_int_passes_if_value_castable_to_int():
    StudyVariableFactory(study_field__field_type='int', value='-12.0').clean()


@pytest.mark.django_db
def test_study_variable_clean_field_type_int_raises_error_if_value_not_castable_to_int():
    with pytest.raises(ValidationError):
        assert StudyVariableFactory(study_field__field_type='int', value='1.6').clean()


@pytest.mark.parametrize("sep, list_value", [
    (',', "MEX,CAN,USA"),
    (',', "MEX, CAN, USA"),
    (' ', "MEX CAN USA"),
])
@pytest.mark.django_db
def test_study_variable_split_list(sep, list_value):
    field = StudyFieldFactory(field_name='country')
    studies = StudyFactory.create_batch(4)
    StudyVariableFactory(with_studies=studies[3:4], study_field=field, value="BLG")
    StudyVariableFactory(with_studies=studies[2:3], study_field=field, value="USA")
    var = StudyVariableFactory(with_studies=studies[:2], study_field=field, value=list_value)
    assert StudyVariable.objects.all().count() == 3
    field.field_type = 'list'
    var.split_list(sep=sep)
    assert StudyVariable.objects.all().count() == 4
    values = list(StudyVariable.objects.all()
                               .order_by('value')
                               .values_list('value', flat=True))
    assert values == ['BLG', 'CAN', 'MEX', 'USA']

@pytest.mark.django_db
def test_study_variable_split_list_does_not_persist_self():
    field = StudyFieldFactory(field_name='country', field_type='list')
    study = StudyFactory.create()
    var = StudyVariableFactory(with_studies=[study], study_field=field, value="USA,, ,  ")
    assert var.pk is None
    assert StudyVariable.objects.all().count() == 1
    var = StudyVariableFactory(with_studies=[study], study_field=field, value="USA,CAN")
    assert var.pk is None
    assert StudyVariable.objects.all().count() == 2


@pytest.mark.django_db
def test_study_variable_split_list_does_not_split_when_missing_delimiter():
    field = StudyFieldFactory(field_name='country', field_type='list')
    study = StudyFactory.create()
    var = StudyVariableFactory(with_studies=[study], study_field=field, value="USA")
    assert var.pk is not None
    assert StudyVariable.objects.all().count() == 1


@pytest.mark.django_db
def test_study_variable_split_list_sets_all_studies():
    field = StudyFieldFactory(field_name='country', field_type='list')

    usa_study = StudyFactory.create()
    usa_var = StudyVariableFactory(with_studies=[usa_study], study_field=field, value="USA")
    assert usa_study in usa_var.studies.all()

    split_study = StudyFactory.create()
    split_var = StudyVariableFactory(with_studies=[split_study], study_field=field, value="USA,CAN")
    assert split_var.pk is None
    assert len(split_var.split_variables) == 2
    assert StudyVariable.objects.all().count() == 2

    split_usa_var = split_var.split_variables[0]
    split_can_var = split_var.split_variables[1]

    assert split_usa_var == usa_var
    assert split_usa_var.value == 'USA'
    assert split_usa_var.studies.all().count() == 2
    assert usa_study in usa_var.studies.all()
    assert split_study in usa_var.studies.all()

    assert split_can_var.value == 'CAN'
    assert split_can_var.studies.all().count() == 1
    assert split_study in split_can_var.studies.all()


@pytest.mark.django_db
def __setup_study_variable_data():
    """
    study_id  | Start Year | Stop Year
    ki-103    |  1956.0    |  2016.0
    ki-114    |  1913.0    |   ---
    CPT       |  1913.0    |  2016.0
    """
    study_1 = StudyFactory(study_id='ki-103')
    study_2 = StudyFactory(study_id='ki-114')
    study_3 = StudyFactory(study_id='CPT')
    StudyVariableFactory(with_studies=[study_1],
                         study_field__field_name='START_YEAR',
                         study_field__label='Start Year',
                         value='1956.0')
    StudyVariableFactory(with_studies=[study_2, study_3],
                         study_field__field_name='START_YEAR',
                         study_field__label='Start Year',
                         value='1913.0')
    StudyVariableFactory(with_studies=[study_1, study_3],
                         study_field__field_name='STOP_YEAR',
                         study_field__label='Stop Year',
                         value='2016.0')


@pytest.mark.django_db
def test_study_variable_get_dataframe_one_column_by_study_field():
    __setup_study_variable_data()
    study_fields = StudyField.objects.filter(field_name='START_YEAR')
    df = StudyVariable.get_dataframe(study_field__in=study_fields)
    assert list(df.columns) == ['Start Year']
    assert list(df.index) == ['CPT', 'ki-103', 'ki-114']
    assert list(df.values) == ['1913.0', '1956.0', '1913.0']


@pytest.mark.django_db
def test_study_variable_get_dataframe_column_contains_null():
    __setup_study_variable_data()
    study_fields = StudyField.objects.filter(field_name__in=['START_YEAR', 'STOP_YEAR'])
    df = StudyVariable.get_dataframe(study_field__in=study_fields)
    assert sorted(list(df.columns)) == sorted(['Start Year', 'Stop Year'])
    assert list(df.index) == ['CPT', 'ki-103', 'ki-114']
    assert list(df['Start Year'].values) == ['1913.0', '1956.0', '1913.0']
    assert list(df['Stop Year'].values) == ['2016.0', '2016.0', None]


@pytest.mark.django_db
def test_study_variable_get_dataframe_where_field_not_in_study_variables():
    __setup_study_variable_data()
    StudyFieldFactory(field_name='FOO', label='FOO')
    study_fields = StudyField.objects.filter(field_name__in=['FOO'])
    df = StudyVariable.get_dataframe(study_field__in=study_fields)
    assert df is None


@pytest.mark.django_db
def test_study_variable_get_dataframe_where_one_int_field_not_in_study_variables():
    __setup_study_variable_data()
    StudyFieldFactory(field_name='FOO', label='FOO', field_type='int')
    study_fields = StudyField.objects.filter(field_name__in=['FOO', 'START_YEAR'])
    df = StudyVariable.get_dataframe(study_field__in=study_fields)
    assert sorted(list(df.columns)) == sorted(['Start Year'])
    assert list(df.index) == ['CPT', 'ki-103', 'ki-114']
    assert list(df['Start Year'].values) == ['1913.0', '1956.0', '1913.0']


@pytest.mark.django_db
def test_study_variable_get_dataframe_with_field_type_int_reformats_values_to_drop_trailing_zeros():
    StudyFieldFactory(field_name='STOP_YEAR', label='Stop Year', field_type='int')

    __setup_study_variable_data()
    study_fields = StudyField.objects.filter(field_name__in=['START_YEAR', 'STOP_YEAR'])
    assert StudyVariable.objects.filter(study_field__field_type='int').count() == 1

    df = StudyVariable.get_dataframe(study_field__in=study_fields)
    assert sorted(list(df.columns)) == sorted(['Start Year', 'Stop Year'])
    assert list(df.index) == ['CPT', 'ki-103', 'ki-114']
    assert list(df['Start Year'].values) == ['1913.0', '1956.0', '1913.0']
    assert list(df['Stop Year'].values) == ['2016', '2016', None]


@pytest.mark.django_db
def test_study_variable_get_dataframe_with_field_type_float_changes_dtype_to_float():
    StudyFieldFactory(field_name='STOP_YEAR', label='Stop Year', field_type='float')

    __setup_study_variable_data()
    study_fields = StudyField.objects.filter(field_name__in=['START_YEAR', 'STOP_YEAR'])
    assert StudyVariable.objects.filter(study_field__field_type='float').count() == 1

    df = StudyVariable.get_dataframe(study_field__in=study_fields)
    assert sorted(list(df.columns)) == sorted(['Start Year', 'Stop Year'])
    assert list(df.index) == ['CPT', 'ki-103', 'ki-114']
    assert list(df['Start Year'].values) == ['1913.0', '1956.0', '1913.0']
    assert list(df['Stop Year'].values) == [2016.0, 2016.0, None]


@pytest.mark.django_db
def test_study_variable_get_dataframe_one_row_by_study():
    __setup_study_variable_data()
    study_fields = StudyField.objects.filter(field_name__in=['START_YEAR', 'STOP_YEAR'])
    df = StudyVariable.get_dataframe(studies__study_id='ki-103', study_field__in=study_fields)
    assert sorted(list(df.columns)) == sorted(['Start Year', 'Stop Year'])
    assert list(df.index) == ['ki-103']
    assert list(df['Start Year'].values) == ['1956.0']
    assert list(df['Stop Year'].values) == ['2016.0']


@pytest.mark.django_db
def test_study_variable_get_dataframe_two_rows_by_study_id():
    __setup_study_variable_data()
    study_fields = StudyField.objects.filter(field_name__in=['START_YEAR', 'STOP_YEAR'])
    df = StudyVariable.get_dataframe(studies__study_id__in=['ki-103', 'ki-114'],
                                     study_field__in=study_fields)
    assert sorted(list(df.columns)) == sorted(['Start Year', 'Stop Year'])
    assert list(df.index) == ['ki-103', 'ki-114']
    assert list(df['Start Year'].values) == ['1956.0', '1913.0']
    assert list(df['Stop Year'].values) == ['2016.0', None]


@pytest.mark.django_db
def test_study_variable_get_dataframe_uses_max_value():
    str_field = StudyFieldFactory(field_name='STR_FIELD', field_type="str", label='Str Field')
    list_field = StudyFieldFactory(field_name='LIST_FIELD', field_type="list", label='List Field')
    int_field = StudyFieldFactory(field_name='INT_FIELD', field_type="int", label='Int Field')
    float_field = StudyFieldFactory(field_name='FLOAT_FIELD', field_type="float", label='Float Field')
    studies = StudyFactory.create_batch(4)

    StudyVariableFactory(with_studies=studies[2:], study_field=str_field, value='abc')
    StudyVariableFactory(with_studies=studies[2:], study_field=list_field, value="AAA")
    StudyVariableFactory(with_studies=studies[2:], study_field=int_field, value=1)
    StudyVariableFactory(with_studies=studies[2:], study_field=int_field, value=3)
    StudyVariableFactory(with_studies=studies[2:], study_field=float_field, value=100.1)
    StudyVariableFactory(with_studies=studies[2:], study_field=float_field, value=300.3)

    StudyVariableFactory(with_studies=studies[:1], study_field=str_field, value='xyz')
    StudyVariableFactory(with_studies=studies[:1], study_field=list_field, value="DDD, CCC, AAA")
    StudyVariableFactory(with_studies=studies[:1], study_field=int_field, value=5)
    StudyVariableFactory(with_studies=studies[:1], study_field=int_field, value=7)
    StudyVariableFactory(with_studies=studies[:1], study_field=float_field, value=500.5)
    StudyVariableFactory(with_studies=studies[:1], study_field=float_field, value=700.7)

    df = StudyVariable.get_dataframe(study_field__in=StudyField.objects.filter(field_name__in=['STR_FIELD',
                                                                                               'LIST_FIELD',
                                                                                               'INT_FIELD',
                                                                                               'FLOAT_FIELD']))
    assert list(df.columns) == ['Float Field', 'Int Field', 'List Field', 'Str Field']
    assert df.values.tolist() == [
        [700.7, '7', 'AAA, DDD, CCC', 'xyz'],
        [300.3, '3', 'AAA', 'abc'],
        [300.3, '3', 'AAA', 'abc']
    ]


@pytest.mark.django_db
def test_study_variable_is_created_with_studies():
    studies = StudyFactory.create_batch(4)

    # Via factory
    study_var = StudyVariableFactory(with_studies=studies)
    study_var_studies = study_var.studies.all()
    for study in studies:
        assert study in study_var_studies
    assert study_var._with_studies == []

    # Via class
    field = StudyFieldFactory(field_name='test')
    study_var = StudyVariable(with_studies=studies, study_field=field, value='test')
    study_var.save()
    study_var_studies = study_var.studies.all()
    for study in studies:
        assert study in study_var_studies
    assert study_var._with_studies == []


@pytest.mark.django_db
def test_variable_create():
    variable = VariableFactory(domain__code='TEST',
                               domain__label='test_label',
                               code='0')
    assert str(variable) == '%s| TEST: 0' % variable.id


@pytest.mark.django_db
def test_variable_create_with_category():
    variable = VariableFactory(domain__code='TEST',
                               domain__label='test_label',
                               code='0',
                               category='B')
    assert str(variable) == '%s| TEST - B: 0' % variable.id


@pytest.mark.django_db
def test_variable_create_clash():
    VariableFactory(code='0', label='A')
    with pytest.raises(IntegrityError):
        VariableFactory(code='0', label='some description')


@pytest.mark.django_db
def test_count_create():
    query = CountFactory(study__study_id='test', count=10, subjects=5)
    assert str(query) == 'test: 10'


@pytest.mark.django_db
def test_count_create_no_subjects():
    with pytest.raises(IntegrityError):
        CountFactory(count=10, subjects=None)


@pytest.mark.django_db
def test_domain_create():
    domain = DomainFactory(code='TEST', label='test_label')
    assert str(domain) == 'TEST'


@pytest.mark.django_db
def test_domain_clash():
    DomainFactory(code='SAMPLE', label='sample')
    with pytest.raises(IntegrityError):
        DomainFactory(code='SAMPLE', label='sample')


# FILTER SECTION
@pytest.mark.django_db
def test_filter_create():
    filt = FilterFactory(study_field=None, label='Sample')
    assert str(filt) == 'Sample'


@pytest.mark.django_db()
def test_domain_filter_without_label_grabs_label_from_domain():
    filt = FilterFactory(domain__label='bananas', study_field=None, label=None)
    assert filt.label == 'bananas'


@pytest.mark.django_db()
def test_study_filter_without_label_grabs_label_from_study_field():
    filt = FilterFactory(study_field__label='Start Year', domain=None, label=None)
    assert filt.label == 'Start Year'


@pytest.mark.django_db()
def test_study_filter_name_is_study_field_field_name():
    filt = FilterFactory(study_field__field_name='START_YEAR', domain=None)
    assert filt.name == 'START_YEAR'


@pytest.mark.django_db()
def test_domain_filter_name_is_domain_code():
    filt = FilterFactory(domain__code='BRD', study_field=None)
    assert filt.name == 'BRD'


@pytest.mark.django_db()
def test_filter_qualifier_name_is_domain_code():
    filt = FilterFactory(domain__code='BRD', domain__is_qualifier=True, study_field=None)
    assert filt.name == 'BRD'


@pytest.mark.django_db
def test_filter_study_filter_type():
    filt = FilterFactory(domain=None)
    assert filt.filter_type == 'Study'


@pytest.mark.django_db
def test_filter_domain_filter_type():
    filt = FilterFactory(study_field=None)
    assert filt.filter_type == 'Domain'


@pytest.mark.django_db
def test_filter_qualifier_filter_type():
    filt = FilterFactory(domain__is_qualifier=True, study_field=None)
    assert filt.filter_type == 'Qualifier'


@pytest.mark.django_db()
def test_filter_get_values_on_study_filter():
    __setup_study_variable_data()
    filt = FilterFactory(domain=None, study_field__field_name='START_YEAR')

    assert filt.get_values() == ['1913.0', '1956.0']


@pytest.mark.django_db
def test_filter_get_values_on_non_qualifier_domain_filter():
    domain = DomainFactory(code='foo', is_qualifier=False)
    variable1 = VariableFactory(domain=domain, code='ZZZ', label='aaa')
    variable2 = VariableFactory(domain=domain, code='YYY', label='ccc')
    variable3 = VariableFactory(domain=domain, code='XXX', label='bbb')
    VariableFactory(code='2', label='C')

    filt = FilterFactory(domain=domain, study_field=None)

    # note that studies are sorted by `label`
    assert filt.get_values() == [variable1.code, variable3.code, variable2.code]


@pytest.mark.django_db
def test_filter_get_values_on_qualifer_domain_filter():
    domain = DomainFactory(code='FOO', is_qualifier=True)
    variable1 = VariableFactory(domain=domain, code='0', label='aaa')
    variable2 = VariableFactory(domain=domain, code='2', label='bbb')
    variable3 = VariableFactory(domain=domain, code='1', label='ccc')
    VariableFactory(code='2', label='C')

    filt = FilterFactory(domain=domain, study_field=None)

    # note that studies are sorted by int(`code`)
    assert filt.get_values() == [variable1.code, variable3.code, variable2.code]


@pytest.mark.django_db()
@pytest.mark.parametrize("pass_values_kwarg", [(True), (False)])
def test_filter_get_choices_on_study_filter(pass_values_kwarg):
    __setup_study_variable_data()
    filt = FilterFactory(domain=None, study_field__field_name='START_YEAR')

    values = filt.get_values() if pass_values_kwarg else None
    # note that studies are sorted by studyvariable__value
    assert filt.get_choices(values=values) == [('1913.0', '1913.0'),
                                               ('1956.0', '1956.0')]


@pytest.mark.django_db
@pytest.mark.parametrize("pass_values_kwarg", [(True), (False)])
def test_filter_get_choices_from_non_qualifier_domain_filter(pass_values_kwarg):
    domain = DomainFactory(code='FOO', is_qualifier=False)
    VariableFactory(domain=domain, code='ZZZ', label='aaa')
    VariableFactory(domain=domain, code='YYY', label='ccc')
    VariableFactory(domain=domain, code='XXX', label='bbb')
    filt = FilterFactory(domain=domain, study_field=None)

    values = filt.get_values() if pass_values_kwarg else None
    # note that studies are sorted by `label`
    assert filt.get_choices(values=values) == [('ZZZ', 'aaa'), ('XXX', 'bbb'), ('YYY', 'ccc')]


@pytest.mark.django_db
@pytest.mark.parametrize("pass_values_kwarg", [(True), (False)])
def test_filter_get_counts_study_no_active_filters(rf, pass_values_kwarg):
    field = StudyFieldFactory(field_name='STUDY_TYPE')
    studies = StudyFactory.create_batch(4)

    StudyVariableFactory(with_studies=studies[:2], study_field=field, value="A")
    StudyVariableFactory(with_studies=studies[2:], study_field=field, value="B")

    filt = FilterFactory(study_field=field, domain=None)

    request = rf.get(reverse('study-filter'))

    values = filt.get_values() if pass_values_kwarg else None
    # note that studies are sorted by `study_type`
    assert filt.get_counts(request, values=values) == [2, 2]


@pytest.mark.django_db
def test_filter_get_counts_study_no_active_filters_with_field_type_list(rf):
    field = StudyFieldFactory(field_name='COUNTRY')
    studies = StudyFactory.create_batch(4)
    StudyVariableFactory(with_studies=studies[2:], study_field=field, value="USA")
    StudyVariableFactory(with_studies=studies[:2], study_field=field, value="CAN, MEX, USA")
    field.field_type = "list"
    field.save()
    assert StudyVariable.objects.all().count() == 3
    filt = FilterFactory(study_field=field, domain=None)

    request = rf.get(reverse('study-filter'))

    # note that studies are sorted by `studyvariable__value`
    assert filt.get_counts(request) == [2, 2, 4]


@pytest.mark.django_db
def test_filter_get_counts_study_with_active_filter_same_as_field_filter(rf):
    field = StudyFieldFactory(field_name='study_type')
    studies = StudyFactory.create_batch(5)

    var1 = StudyVariableFactory(with_studies=studies[:3], study_field=field, value="A")
    StudyVariableFactory(with_studies=studies[3:], study_field=field, value="B")

    filt = FilterFactory(study_field=field, domain=None)

    get_params = {'study_type': [var1.id]}
    request = rf.get(reverse('study-filter'), data=get_params)

    # note that studies are sorted by `study_type`
    assert filt.get_counts(request) == [3, 2]


@pytest.mark.django_db
def test_filter_get_counts_study_with_active_filter_different_from_field_filter(rf):
    field = StudyFieldFactory(field_name='STUDY_TYPE')
    field2 = StudyFieldFactory(field_name='INTERVENTION_TYPE')

    study = StudyFactory()
    study2 = StudyFactory()

    StudyVariableFactory(study_field=field, value="A", with_studies=[study])
    StudyVariableFactory(study_field=field, value="B", with_studies=[study2])
    var1 = StudyVariableFactory(study_field=field2, value="FOO", with_studies=[study])
    StudyVariableFactory(study_field=field2, value="BAR", with_studies=[study2])

    filt = FilterFactory(study_field=field, domain=None)
    FilterFactory(study_field=field2, domain=None)

    get_params = {'INTERVENTION_TYPE': [var1.id]}
    request = rf.get(reverse('study-filter'), data=get_params)

    # note that studies are sorted by `study_type`
    assert filt.get_counts(request) == [1, 0]


@pytest.mark.django_db
def test_filter_get_counts_domain_no_active_filters(rf):
    domain = DomainFactory(code="DOMAIN", is_qualifier=False)
    variable1 = VariableFactory(domain=domain, code='ZZZ', label='aaa')
    variable2 = VariableFactory(domain=domain, code='YYY', label='ccc')

    study1 = StudyFactory()
    study2 = StudyFactory()

    CountFactory(study=study1, codes=[variable1])
    CountFactory(study=study1, codes=[variable2])
    CountFactory(study=study2, codes=[variable1])
    CountFactory(study=study2, codes=[variable2])

    filt = FilterFactory(domain=domain, study_field=None)

    request = rf.get(reverse('study-filter'))

    # note that studies are sorted by `label`
    assert filt.get_counts(request) == [2, 2]


@pytest.mark.django_db
def test_filter_get_counts_domain_with_active_filter_same_as_field_filter(rf):
    domain = DomainFactory(code="DOMAIN", is_qualifier=False)
    variable1 = VariableFactory(domain=domain, code='ZZZ', label='aaa')
    variable2 = VariableFactory(domain=domain, code='YYY', label='ccc')

    study1 = StudyFactory()
    study2 = StudyFactory()

    CountFactory(study=study1, codes=[variable1])
    CountFactory(study=study1, codes=[variable2])
    CountFactory(study=study2, codes=[variable1])
    CountFactory(study=study2, codes=[variable2])

    filt = FilterFactory(domain=domain, study_field=None)

    get_params = {'code': ['ZZZ']}
    request = rf.get(reverse('study-filter'), data=get_params)

    # note that studies are sorted by `label`
    assert filt.get_counts(request) == [2, 2]


@pytest.mark.django_db
def test_filter_get_counts_domain_with_active_filter_different_from_field_filter(rf):
    domain = DomainFactory(code="DOMAIN", is_qualifier=False)
    variable1 = VariableFactory(domain=domain, code='ZZZ', label='aaa')
    variable2 = VariableFactory(domain=domain, code='YYY', label='ccc')

    domain2 = DomainFactory(code="BAR", is_qualifier=False)
    variable3 = VariableFactory(domain=domain2, code='AAA', label='111')
    variable4 = VariableFactory(domain=domain2, code='BBB', label='222')

    study1 = StudyFactory()
    study2 = StudyFactory()

    CountFactory(study=study1, codes=[variable1])
    CountFactory(study=study2, codes=[variable2])
    CountFactory(study=study1, codes=[variable3])
    CountFactory(study=study2, codes=[variable4])

    filt = FilterFactory(domain=domain, study_field=None)
    FilterFactory(domain=domain2, study_field=None)

    get_params = {'BAR': [variable3.id]}
    request = rf.get(reverse('study-filter'), data=get_params)

    # note that studies are sorted by `label`
    assert filt.get_counts(request) == [1, 0]


@pytest.mark.django_db
def test_filter_get_categories_from_domain_without_categories():
    domain = DomainFactory()
    VariableFactory.create_batch(3, domain=domain, category=None)

    filt = FilterFactory(domain=domain, study_field=None)
    assert filt.get_categories() == []


@pytest.mark.django_db
def test_filter_get_categories_from_domain_with_categories():
    domain = DomainFactory()
    VariableFactory(domain=domain, code='0', label='A', category='Cat1')
    VariableFactory(domain=domain, code='1', label='B', category='Cat1')
    VariableFactory(domain=domain, code='-2', label='C', category='Cat2')
    VariableFactory(domain=domain, code='11', label='D', category='Cat3')

    filt = FilterFactory(domain=domain, study_field=None)
    assert filt.get_categories() == ['Cat1', 'Cat1', 'Cat2', 'Cat3']


@pytest.mark.django_db
def test_filter_get_selections_with_checkbox_widget(rf):
    field = StudyFieldFactory(field_name='STUDY_TYPE')

    var1 = StudyVariableFactory(study_field=field, value="D")
    var2 = StudyVariableFactory(study_field=field, value="A")
    StudyVariableFactory(study_field=field, value="B")

    filt = FilterFactory(study_field=field, domain=None, widget='checkbox')

    get_params = {'STUDY_TYPE': [var2.id, var1.id]}
    request = rf.get(reverse('study-filter'), data=get_params)

    assert filt.get_selections(request.GET) == [str(var2.id), str(var1.id)]


@pytest.mark.django_db
def test_filter_get_selections_with_discrete_slider_widget(rf):
    domain = DomainFactory(code='LALA')
    VariableFactory(domain=domain, code='0', label='A')
    VariableFactory(domain=domain, code='1', label='B')
    VariableFactory(domain=domain, code='-2', label='C')
    VariableFactory(domain=domain, code='11', label='D')

    filt = FilterFactory(domain=domain, study_field=None, widget='discrete slider')

    get_params = {'LALA': 'B;D'}
    request = rf.get(reverse('study-filter'), data=get_params)

    assert filt.get_selections(request.GET) == ['1', '-2', '11']


@pytest.mark.django_db
def test_filter_get_selections_with_double_slider_widget(rf):
    field = StudyFieldFactory(field_name='START_YEAR')

    StudyVariableFactory(study_field=field, value='1991.0')
    StudyVariableFactory(study_field=field, value='1992.0')
    StudyVariableFactory(study_field=field, value='1993.0')
    StudyVariableFactory(study_field=field, value='1994.0')

    filt = FilterFactory(study_field=field, domain=None, widget='double slider')

    get_params = {'START_YEAR': '1992.0;1993.0'}
    request = rf.get(reverse('study-filter'), data=get_params)

    assert filt.get_selections(request.GET) == ['1992.0', '1993.0']


@pytest.mark.django_db
def test_filter_filter_queryset_with_study_field_filter_with_checkbox_widget(rf):
    field = StudyFieldFactory(field_name='STUDY_TYPE')

    variable = StudyVariableFactory(study_field=field, value="A", with_studies=[StudyFactory()])
    StudyVariableFactory(study_field=field, value="B", with_studies=[StudyFactory()])

    filt = FilterFactory(study_field=field, domain=None, widget='checkbox')

    get_params = {'STUDY_TYPE': [variable.id]}
    request = rf.get(reverse('study-filter'), data=get_params)

    studies = Study.objects.all()
    filtered = filt.filter_queryset(studies, request.GET)
    assert filtered.first() == variable.studies.first()
    assert filtered.count() == 1
    assert variable.studies.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("to_value, result", [
    ('1994.0', True),
    ('1993.0', False),
    ])
def test_filter_double_slider_is_full_range(rf, to_value, result):
    field = StudyFieldFactory(field_name='START_YEAR')

    StudyVariableFactory(study_field=field, value='1991.0')
    StudyVariableFactory(study_field=field, value='1992.0')
    StudyVariableFactory(study_field=field, value='1993.0')
    StudyVariableFactory(study_field=field, value='1994.0')

    filt = FilterFactory(study_field=field, domain=None, widget='double slider')

    assert filt.is_full_range('1991.0', to_value) is result


@pytest.mark.django_db
@pytest.mark.parametrize("to_value, result", [
    ('D', True),
    ('C', False),
    ])
def test_filter_discrete_slider_is_full_range(rf, to_value, result):
    domain = DomainFactory(code="DOMAIN", is_qualifier=True)
    VariableFactory(domain=domain, code='0', label="A")
    VariableFactory(domain=domain, code='1', label="B")
    VariableFactory(domain=domain, code='2', label="C")
    VariableFactory(domain=domain, code='3', label="D")

    filt = FilterFactory(domain=domain, study_field=None, widget='discrete slider')

    assert filt.is_full_range('A', to_value) is result


@pytest.mark.django_db
def test_filter_filter_queryset_with_study_field_filter_with_int_double_slider_widget(rf):
    field = StudyFieldFactory(field_name='START_YEAR')
    studies = StudyFactory.create_batch(4)

    StudyVariableFactory(study_field=field, value='1991.0', with_studies=studies[:1])
    StudyVariableFactory(study_field=field, value='1992.0', with_studies=studies[1:2])
    StudyVariableFactory(study_field=field, value='1993.0', with_studies=studies[2:3])
    StudyVariableFactory(study_field=field, value='1994.0', with_studies=studies[3:])

    filt = FilterFactory(study_field=field, domain=None, widget='double slider')

    get_params = {'START_YEAR': ['1992;1993']}

    request = rf.get(reverse('study-filter'), data=get_params)

    studies = Study.objects.all()

    filtered = filt.filter_queryset(studies, request.GET)
    assert list(filtered.order_by('id')) == list(studies[1:3])


@pytest.mark.django_db
def test_filter_filter_queryset_with_study_field_filter_with_float_double_slider_widget(rf):
    field = StudyFieldFactory(field_name='DISTANCE')
    studies = StudyFactory.create_batch(4)

    StudyVariableFactory(study_field=field, value='3.5', with_studies=studies[:1])
    StudyVariableFactory(study_field=field, value='2.1', with_studies=studies[1:2])
    StudyVariableFactory(study_field=field, value='7.9', with_studies=studies[2:3])
    StudyVariableFactory(study_field=field, value='4.1', with_studies=studies[3:])

    filt = FilterFactory(study_field=field, domain=None, widget='double slider')

    get_params = {'DISTANCE': ['2.1;4.0']}

    request = rf.get(reverse('study-filter'), data=get_params)

    studies = Study.objects.all()

    filtered = filt.filter_queryset(studies, request.GET)
    assert list(filtered.order_by('id')) == list(studies[:2])


@pytest.mark.django_db
def test_filter_filter_queryset_with_study_field_filter_with_field_type_list(rf):
    field = StudyFieldFactory(field_name='ANIMAL')
    studies = StudyFactory.create_batch(4)

    StudyVariableFactory(study_field=field, with_studies=studies[:1], value='cat, dog')
    StudyVariableFactory(study_field=field, with_studies=studies[2:], value='penguin, goat')
    field.field_type = "list"
    field.save()

    filt = FilterFactory(study_field=field, domain=None, widget='checkbox')

    cat_var = StudyVariable.objects.get(study_field=field, value='cat')
    peng_var = StudyVariable.objects.get(study_field=field, value='penguin')

    get_params = {'ANIMAL': [cat_var.id, peng_var.id]}

    request = rf.get(reverse('study-filter'), data=get_params)

    studies = Study.objects.all()

    filtered = filt.filter_queryset(studies, request.GET)
    assert list(filtered.order_by('id')) == [studies[0], studies[2], studies[3]]


@pytest.mark.django_db
def test_filter_filter_queryset_with_study_field_filter_with_field_type_list_contained_in_word(rf):
    field = StudyFieldFactory(field_name='FRUIT')
    studies = StudyFactory.create_batch(4)

    StudyVariableFactory(study_field=field, with_studies=studies[:1], value='pineapple, orange')
    var_1 = StudyVariableFactory(study_field=field, with_studies=studies[1:2], value='apple')
    StudyVariableFactory(study_field=field, with_studies=studies[2:3], value='pear')
    StudyVariableFactory(study_field=field, with_studies=studies[3:], value='grape, kiwi')
    field.field_type = "list"
    field.save()

    filt = FilterFactory(study_field=field, domain=None, widget='checkbox')

    get_params = {'FRUIT': [var_1.id]}

    request = rf.get(reverse('study-filter'), data=get_params)

    studies = Study.objects.all()

    filtered = filt.filter_queryset(studies, request.GET)
    assert list(filtered.order_by('id')) == [studies[1]]


@pytest.mark.django_db
def test_filter_filter_queryset_with_domain_filter_with_checkbox_widget(rf):
    domain = DomainFactory(code="DOMAIN")
    variable1 = VariableFactory(domain=domain, code='FOO')
    variable2 = VariableFactory(domain=domain, code='BAR')

    count1 = CountFactory(study__study_id="S1", codes=[variable1])
    CountFactory(study__study_id="S2", codes=[variable2])

    filt = FilterFactory(domain=domain, study_field=None, widget='checkbox')

    get_params = {'DOMAIN': [variable1.id]}
    request = rf.get(reverse('study-filter'), data=get_params)

    studies = Study.objects.all()

    filtered = filt.filter_queryset(studies, request.GET)
    assert list(filtered) == [count1.study]


@pytest.mark.django_db
def test_filter_filter_queryset_with_qualifier_domain_filter_with_discrete_slider_widget(rf):
    domain = DomainFactory(code="DOMAIN", is_qualifier=True)
    variable1 = VariableFactory(domain=domain, code='0', label="A")
    variable2 = VariableFactory(domain=domain, code='1', label="B")
    variable3 = VariableFactory(domain=domain, code='2', label="C")
    variable4 = VariableFactory(domain=domain, code='3', label="D")

    CountFactory(codes=[variable1])
    count2 = CountFactory(codes=[variable2])
    count3 = CountFactory(codes=[variable3])
    CountFactory(codes=[variable4])

    filt = FilterFactory(domain=domain, study_field=None, widget='discrete slider')

    # ion slider returns labels at GET params, not codes
    get_params = {'DOMAIN': ['B;C']}
    request = rf.get(reverse('study-filter'), data=get_params)

    studies = Study.objects.all()

    filtered = filt.filter_queryset(studies, request.GET)
    assert list(filtered.order_by('id')) == [count2.study, count3.study]


@pytest.mark.django_db
def test_filter_filter_queryset_with_qualifier_domain_filter_with_double_slider_widget(rf):
    domain = DomainFactory(code="DOMAIN", is_qualifier=True)
    variable1 = VariableFactory(domain=domain, code='0', label="A")
    variable2 = VariableFactory(domain=domain, code='1', label="B")
    variable3 = VariableFactory(domain=domain, code='2', label="C")
    variable4 = VariableFactory(domain=domain, code='3', label="D")

    CountFactory(codes=[variable1])
    count2 = CountFactory(codes=[variable2])
    count3 = CountFactory(codes=[variable3])
    CountFactory(codes=[variable4])

    filt = FilterFactory(domain=domain, study_field=None, widget='double slider')

    # ion slider returns labels at GET params, not codes
    get_params = {'DOMAIN': ['1;2']}
    request = rf.get(reverse('study-filter'), data=get_params)

    studies = Study.objects.all()

    filtered = filt.filter_queryset(studies, request.GET)
    assert list(filtered.order_by('id')) == [count2.study, count3.study]


@pytest.mark.django_db
def test_filter_get_applied_filters_with_checkbox_widget(rf):
    field = StudyFieldFactory(field_name='STUDY_TYPE')

    var1 = StudyVariableFactory(study_field=field, value="D")
    var2 = StudyVariableFactory(study_field=field, value="A")
    StudyVariableFactory(study_field=field, value="B")

    filt = FilterFactory(study_field=field, domain=None, widget='checkbox')

    get_params = {'STUDY_TYPE': [var2.id, var1.id]}
    request = rf.get(reverse('study-filter'), data=get_params)

    assert filt.get_applied_filters(request.GET) == 'A | D'


@pytest.mark.django_db
def test_filter_get_applied_filters_with_discrete_slider_widget(rf):
    domain = DomainFactory(code='LALA')
    VariableFactory(domain=domain, code='0', label='A')
    VariableFactory(domain=domain, code='1', label='B')
    VariableFactory(domain=domain, code='-2', label='C')
    VariableFactory(domain=domain, code='11', label='D')

    filt = FilterFactory(domain=domain, study_field=None, widget='discrete slider')

    get_params = {'LALA': 'B;D'}
    request = rf.get(reverse('study-filter'), data=get_params)

    assert filt.get_applied_filters(request.GET) == 'B - D'


@pytest.mark.django_db
def test_filter_get_applied_filters_with_double_slider_widget(rf):
    field = StudyFieldFactory(field_name='START_YEAR')

    StudyVariableFactory(study_field=field, value='1991.0')
    StudyVariableFactory(study_field=field, value='1992.0')
    StudyVariableFactory(study_field=field, value='1993.0')
    StudyVariableFactory(study_field=field, value='1994.0')

    filt = FilterFactory(study_field=field, domain=None, widget='double slider')

    get_params = {'START_YEAR': '1992.0;1993.0'}
    request = rf.get(reverse('study-filter'), data=get_params)

    assert filt.get_applied_filters(request.GET) == '1992.0 - 1993.0'


@pytest.mark.django_db
def test_filter_get_initial_slider_values_not_active_filter(rf):
    domain = DomainFactory(code='LALA')
    filt = FilterFactory(domain=domain, study_field=None, widget='discrete slider')

    request = rf.get(reverse('study-filter'))

    assert filt.get_initial_slider_values(request.GET) == {}


@pytest.mark.django_db
@pytest.mark.parametrize("pass_values_kwarg", [(True), (False)])
def test_filter_get_initial_slider_values_discrete_widget(rf, pass_values_kwarg):
    domain = DomainFactory(code='LALA')
    VariableFactory(domain=domain, code='0', label='A')
    VariableFactory(domain=domain, code='1', label='B')
    VariableFactory(domain=domain, code='-2', label='C')
    VariableFactory(domain=domain, code='11', label='D')

    filt = FilterFactory(domain=domain, study_field=None, widget='discrete slider')

    get_params = {'LALA': 'B;D'}
    request = rf.get(reverse('study-filter'), data=get_params)

    values = filt.get_values() if pass_values_kwarg else None

    assert filt.get_initial_slider_values(request.GET, values=values) == {'from_value': 1, 'to_value': 3}


@pytest.mark.django_db
@pytest.mark.parametrize("pass_values_kwarg", [(True), (False)])
def test_filter_get_initial_slider_values_double_widget(rf, pass_values_kwarg):
    field = StudyFieldFactory(field_name='START_YEAR')

    StudyVariableFactory(study_field=field, value='1991.0')
    StudyVariableFactory(study_field=field, value='1992.0')
    StudyVariableFactory(study_field=field, value='1993.0')
    StudyVariableFactory(study_field=field, value='1994.0')

    filt = FilterFactory(study_field=field, domain=None, widget='double slider')

    get_params = {'START_YEAR': '1992.0;1993.0'}
    request = rf.get(reverse('study-filter'), data=get_params)

    values = filt.get_values() if pass_values_kwarg else None

    assert filt.get_initial_slider_values(request.GET, values=values) == {'to_value': 1993, 'from_value': 1992}


@pytest.mark.django_db
def test_filter_numeric_qualifier_filter_range_widget():
    domain = DomainFactory(code='TEST', label='Test', is_qualifier=True)
    variable1 = VariableFactory(domain=domain, code='0', label='A')
    variable2 = VariableFactory(domain=domain, code='1', label='B')
    VariableFactory(code='2', label='C')
    filt = FilterFactory(domain=domain, study_field=None, label='Test',
                         widget='double_slider')
    assert filt.get_values() == [variable1.code, variable2.code]


@pytest.mark.django_db
def test_filter_clash_with_both_domain_and_study_field_specified():
    filt = FilterFactory()
    with pytest.raises(ValidationError):
        filt.clean()


@pytest.mark.django_db
def test_filter_non_numeric_study_field_range_widget_exception():
    # Ensure non-numeric study field cannot be assigned to double slider
    study_field = StudyFieldFactory(field_name='STUDY_TYPE')
    StudyVariableFactory(study_field=study_field, value='A')
    filt = FilterFactory(study_field=study_field, label='Study Type',
                         domain=None, widget='double slider')
    with pytest.raises(ValidationError):
        filt.clean()


@pytest.mark.django_db
def test_study_filter_studies_joins_filters_with_logial_AND(rf):

    domain = DomainFactory(code="DOMAIN", is_qualifier=True)
    studies = StudyFactory.create_batch(4)
    codes = ['0', '1', '2', '3']
    labels = ["A", "B", "C", "D"]

    for code, label, study in zip(codes, labels, studies):
        var = VariableFactory(domain=domain, code=code, label=label)
        CountFactory(codes=[var], study=study)

    FilterFactory(domain=domain, study_field=None, widget='double slider')

    field = StudyFieldFactory(field_name='STUDY_TYPE')
    values = ["ala", "sbd", "zzz", "bet"]

    study_vars = []
    for value, study in zip(values, studies):
        study_vars.append(StudyVariableFactory(study_field=field, value=value, with_studies=[study]))

    FilterFactory(study_field=field, domain=None, widget='checkbox')

    get_params = {'STUDY_TYPE': [study_vars[0].id, study_vars[1].id], 'DOMAIN': ['1;2']}
    request = rf.get(reverse('study-filter'), data=get_params)

    filtered_studies = Study.filter_studies(Filter.objects.all(), request.GET)
    assert list(filtered_studies) == studies[1:2]


@pytest.mark.django_db
def test_study_filter_studies_returns_all_studies_when_no_filters_given(rf):
    StudyFactory.create_batch(4)
    request = rf.get(reverse('study-filter'))

    empty_queryset = Filter.objects.all()

    filtered_studies = Study.filter_studies(empty_queryset, request.GET)
    assert list(filtered_studies) == list(Study.objects.all())
