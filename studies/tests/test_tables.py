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

from ..tables import StudyTable
from ..models import StudyField, StudyVariable

from .factories import StudyFactory, StudyVariableFactory


@pytest.mark.django_db
def test_study_table_shows_all_fields_if_no_order_defined():
    StudyVariableFactory(with_studies=StudyFactory.create_batch(2),
                         study_field__field_name='start_year')
    StudyVariableFactory(with_studies=StudyFactory.create_batch(2),
                         study_field__field_name='stop_year')

    study_fields = StudyField.objects.all()
    df = StudyVariable.get_dataframe(study_field__in=study_fields)
    df['study_id'] = df.index
    data = df.to_dict('records')
    table = StudyTable(data)

    assert table.sequence == ['study_id', 'Start Year', 'Stop Year']


@pytest.mark.django_db
def test_study_table_shows_ordered_fields_if_big_order_defined():
    StudyVariableFactory(with_studies=StudyFactory.create_batch(2),
                         study_field__field_name='start_year',
                         study_field__big_order=3)
    StudyVariableFactory(with_studies=StudyFactory.create_batch(2),
                         study_field__field_name='stop_year',
                         study_field__big_order=1)
    StudyVariableFactory(with_studies=StudyFactory.create_batch(2))

    study_fields = StudyField.objects.filter(big_order__gte=0)
    df = StudyVariable.get_dataframe(study_field__in=study_fields)
    df['study_id'] = df.index
    data = df.to_dict('records')
    table = StudyTable(data)

    assert table.sequence == ['study_id', 'Stop Year', 'Start Year']
