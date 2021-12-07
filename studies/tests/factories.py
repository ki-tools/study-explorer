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

import factory

from ..models import (
    StudyField,
    Study,
    StudyVariable,
    Domain,
    Variable,
    Count,
    Filter,
)


class StudyFieldFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudyField
    field_name = factory.Sequence(lambda n: "field_name_%s" % n)


class StudyFieldGOCFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudyField
        django_get_or_create = ('field_name',)
    field_name = factory.Sequence(lambda n: "field_name_%s" % n)


class StudyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Study
    study_id = factory.Sequence(lambda n: "ID#%s" % n)


class StudyGOCFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Study
        django_get_or_create = ('study_id',)
    study_id = factory.Sequence(lambda n: "ID#%s" % n)


class StudyVariableFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudyVariable
    study_field = factory.SubFactory(StudyFieldGOCFactory)
    value = '1993'


class DomainFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Domain
    code = factory.Sequence(lambda n: "DOMCODE%s" % n)
    label = 'sample'


class DomainGOCFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Domain
        django_get_or_create = ('code', 'label',)
    code = 'SAMPLE'
    label = 'sample'


class SampleDomainFactory(DomainFactory):
    code = 'SAMPLE'


class QualifierDomainFactory(DomainFactory):
    is_qualifier = True


class AgeDomainFactory(QualifierDomainFactory):
    class Meta:
        django_get_or_create = ('code', 'label')
    code = 'AGECAT'
    label = 'Age'


class FilterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Filter
    domain = factory.SubFactory(DomainGOCFactory)
    study_field = factory.SubFactory(StudyFieldGOCFactory)
    label = 'sample'


class VariableFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Variable
    domain = factory.SubFactory(DomainFactory)
    code = factory.Sequence(lambda n: "VARCODE%s" % n)
    label = factory.Sequence(lambda n: "VARLABEL%s" % n)


class SampleVariableFactory(VariableFactory):
    domain = factory.SubFactory(DomainGOCFactory)
    code = factory.Sequence(lambda n: "Code #%s" % n)
    label = 'A'


class QualifierVariableFactory(VariableFactory):
    domain = factory.SubFactory(QualifierDomainFactory)


class AgeVariableFactory(VariableFactory):
    domain = factory.SubFactory(AgeDomainFactory)


class CountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Count
    study = factory.SubFactory(StudyFactory)
    count = 9
    subjects = 5

    @factory.post_generation
    def codes(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of codes were passed in, use them
            for code in extracted:
                self.codes.add(code)
