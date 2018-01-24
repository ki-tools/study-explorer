import pytest

from ..tables import StudyTable
from ..models import StudyField, StudyVariable

from .factories import StudyFactory, StudyVariableFactory


@pytest.mark.django_db
def test_study_table_shows_all_fields_if_no_order_defined():
    StudyVariableFactory(studies=StudyFactory.create_batch(2),
                         study_field__field_name='start_year')
    StudyVariableFactory(studies=StudyFactory.create_batch(2),
                         study_field__field_name='stop_year')

    study_fields = StudyField.objects.all()
    df = StudyVariable.get_dataframe(study_field__in=study_fields)
    df['study_id'] = df.index
    data = df.to_dict('records')
    table = StudyTable(data)

    assert table.sequence == ['study_id', 'start year', 'stop year']


@pytest.mark.django_db
def test_study_table_shows_ordered_fields_if_big_order_defined():
    StudyVariableFactory(studies=StudyFactory.create_batch(2),
                         study_field__field_name='start_year',
                         study_field__big_order=3)
    StudyVariableFactory(studies=StudyFactory.create_batch(2),
                         study_field__field_name='stop_year',
                         study_field__big_order=1)
    StudyVariableFactory(studies=StudyFactory.create_batch(2))

    study_fields = StudyField.objects.filter(big_order__gte=0)
    df = StudyVariable.get_dataframe(study_field__in=study_fields)
    df['study_id'] = df.index
    data = df.to_dict('records')
    table = StudyTable(data)

    assert table.sequence == ['study_id', 'stop year', 'start year']
