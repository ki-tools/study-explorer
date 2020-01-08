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

import json

import pytest

from ..fields import (
    EmptyChoiceField, RangeField, DiscreteRangeField,
    ExtendedMultipleChoiceField)


def test_empty_choice_field_default_initialization():
    field = EmptyChoiceField(required=False)
    assert field.choices == []


def test_empty_choice_field_with_empty_label_arg():
    field = EmptyChoiceField(required=False, empty_label="Foo")
    assert field.choices == [(None, 'Foo')]


def test_empty_choice_field_with_empty_label_and_choices_args():
    choices = [("A", "A"), ("B", "B")]
    field = EmptyChoiceField(required=False, empty_label="Foo", choices=choices)
    assert field.choices == [(None, 'Foo'), ("A", "A"), ("B", "B")]


def test_extendedmultiplechoice_field_init_method_no_categories_kwarg():
    field = ExtendedMultipleChoiceField()
    assert field.unique_categories == []


def test_extendedmultiplechoice_field_init_method_sorted_categories_and_choices():
    field = ExtendedMultipleChoiceField(categories=["B", "B", "A", "A"],
                                        choices=[(0, '0', 'FOO'), (1, '1', 'BAR'), (2, '2', 'BAT'), (3, '3', 'SPAM')],
                                        counts=[0, 1, 2, 3])

    # Note unique_categories are deduplicated and sorted
    assert field.unique_categories == ["A", "B"]
    assert field.categories == ("A", "A", "B", "B")
    assert field.choices == [(2, '2', 'BAT'), (3, '3', 'SPAM'), (0, '0', 'FOO'), (1, '1', 'BAR')]
    assert field.counts == (2, 3, 0, 1)


def _to_json_string(data):
    return json.dumps(data, sort_keys=True).replace('"null"', 'null')


def test_range_field_without_from_and_to_values():
    field = RangeField(min_value=0, max_value=10)
    data = {'min': 0, 'max': 10, 'type': 'double', 'from': 'null', 'to': 'null'}
    assert field.widget_json == _to_json_string(data)


def test_range_field_with_custom_json():
    field = RangeField(min_value=0, max_value=10, custom_json={'grid': True})
    data = {'min': 0, 'max': 10, 'type': 'double', 'from': 'null', 'to': 'null', 'grid': True}
    assert field.widget_json == _to_json_string(data)


def test_range_field_with_from_and_to_values():
    field = RangeField(min_value=0, max_value=10, from_value=2, to_value=8)
    data = {'min': 0, 'max': 10, 'type': 'double', 'from': 2, 'to': 8}
    assert field.widget_json == _to_json_string(data)


def test_discrete_range_field_choices_without_from_and_to_values():
    choices = [('A', 'A label'), ('B', 'B label')]
    field = DiscreteRangeField(choices=choices)
    data = {'values': list(zip(*choices))[1], 'type': 'double',
            'from': 'null', 'to': 'null'}
    assert field.widget_json == _to_json_string(data)


def test_discrete_range_field_choices_with_custom_json():
    choices = [('A', 'A label'), ('B', 'B label')]
    field = DiscreteRangeField(choices=choices, custom_json={'grid': True})
    data = {'values': list(zip(*choices))[1], 'type': 'double',
            'from': 'null', 'to': 'null', 'grid': True}
    assert field.widget_json == _to_json_string(data)


def test_discrete_range_field_choices_with_from_and_to_values():
    choices = [('A', 'A label'), ('B', 'B label')]
    field = DiscreteRangeField(from_value=0, to_value=1,
                               choices=choices, custom_json={'grid': True})
    data = {'values': list(zip(*choices))[1], 'type': 'double',
            'from': 0, 'to': 1, 'grid': True}
    assert field.widget_json == _to_json_string(data)


def test_discrete_range_field_raise_bad_type_from_value():
    choices = [('A', 'A label'), ('B', 'B label')]
    msg = 'DiscreteRangeField from_value and to_value must be an integer or "null".'
    with pytest.raises(ValueError, match=msg):
        DiscreteRangeField(from_value='A label', choices=choices)


def test_discrete_range_field_raise_out_of_range_from_value():
    choices = [('A', 'A label'), ('B', 'B label')]
    msg = 'DiscreteRangeField from and to values must be less than the length of the list of choices.'
    with pytest.raises(ValueError, match=msg):
        DiscreteRangeField(from_value=3, choices=choices)


def test_discrete_range_field_raise_from_greater_than_to_value():
    choices = [('A', 'A label'), ('B', 'B label')]
    msg = 'DiscreteRangeField from_value cannot be greater than the to_value.'
    with pytest.raises(ValueError, match=msg):
        DiscreteRangeField(from_value=1, to_value=0, choices=choices)
