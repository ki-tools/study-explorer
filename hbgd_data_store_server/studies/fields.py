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

from django import forms


class EmptyChoiceField(forms.ChoiceField):
    def __init__(self, choices=(), empty_label=None, required=True,
                 widget=None, label=None, initial=None, help_text=None,
                 *args, **kwargs):

        # prepend an empty label if it exists (and field is not required!)
        if not required and empty_label is not None:
            choices = tuple([(None, empty_label)] + list(choices))

        super(EmptyChoiceField, self).__init__(
            choices=choices, required=required, widget=widget, label=label,
            initial=initial, help_text=help_text, *args, **kwargs)


class ExtendedMultipleChoiceField(forms.MultipleChoiceField):
    """
    Multiple choice field that additionally keeps track of counts, categories,
    unique_categories and autocomplete values.
    """

    def __init__(self, counts=(), categories=None, autocomplete=None, *args, **kwargs):
        if categories:
            choices = kwargs.get('choices', ())
            # Sort entries by and code
            sorted_opts = sorted(zip(categories, choices, counts),
                                 key=lambda x: (x[0], x[1][1]))
            if sorted_opts:
                categories, choices, counts = zip(*sorted_opts)
            else:
                categories, choices, counts = [], [], []
            kwargs['choices'] = choices

        self.counts = counts
        self.categories = categories
        self.unique_categories = sorted(set(categories)) if categories else []
        self.autocomplete = autocomplete
        super(ExtendedMultipleChoiceField, self).__init__(*args, **kwargs)


class RangeField(forms.IntegerField):

    def __init__(self, *args, from_value='null', to_value='null', custom_json={}, **kwargs):
        self.from_value = from_value
        self.to_value = to_value
        self.custom_json = custom_json
        super(RangeField, self).__init__(*args, **kwargs)

    @property
    def widget_json(self):
        data = {'min': self.min_value,
                'max': self.max_value,
                'type': 'double',
                'from': self.from_value,
                'to': self.to_value}
        data.update(self.custom_json)
        return json.dumps(data, sort_keys=True).replace('"null"', 'null')


class DiscreteRangeField(forms.MultipleChoiceField):

    def __init__(self, *args, from_value='null', to_value='null', custom_json={}, **kwargs):
        super(DiscreteRangeField, self).__init__(*args, **kwargs)
        for val in [from_value, to_value]:
            if not isinstance(val, int) and val != 'null':
                raise ValueError('DiscreteRangeField from_value and to_value must '
                                 'be an integer or "null".')
            elif isinstance(val, int) and not (0 <= val < len(self.choices)):
                raise ValueError('DiscreteRangeField from and to values must be '
                                 'less than the length of the list of choices.')
        if isinstance(from_value, int) and isinstance(to_value, int) and from_value > to_value:
            raise ValueError('DiscreteRangeField from_value cannot be greater'
                             'than the to_value.')
        self.from_value = from_value
        self.to_value = to_value
        self.custom_json = custom_json

    @property
    def widget_json(self):
        labels = [v for _, v in self.choices]
        data = {'type': 'double',
                'values': labels,
                'from': self.from_value,
                'to': self.to_value}
        data.update(self.custom_json)
        return json.dumps(data, sort_keys=True).replace('"null"', 'null')
