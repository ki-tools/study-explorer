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

import django_tables2 as tables

from .models import StudyField, Variable


class StudyTable(tables.Table):
    study_id = tables.Column()

    def __init__(self, *args, **kwargs):
        study_fields = (StudyField.objects.filter(big_order__gte=0).order_by('big_order') or
                        StudyField.objects.order_by('id').all())

        self._meta.sequence = ['study_id']
        for study_field in study_fields:
            self.base_columns[study_field.label] = tables.Column()
            self._meta.sequence.append(study_field.label)

        super(StudyTable, self).__init__(*args, **kwargs)


class VariableTable(tables.Table):
    class Meta:
        model = Variable
        fields = ['category', 'code', 'label']
