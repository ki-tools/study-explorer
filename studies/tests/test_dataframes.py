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

from toolz.itertoolz import groupby
import pandas as pd
import pytest

from ..dataframes import (
    get_counts_df,
    get_counts_by_domain,
    pivot_counts_df,
    get_variable_counts,
    get_variable_count_by_variable
)
from ..models import (
    Study,
    Variable,
)
from .factories import (
    AgeVariableFactory,
    CountFactory,
    QualifierVariableFactory,
    StudyFactory,
    VariableFactory,
)


@pytest.mark.django_db
def test_get_counts_df():
    age_var = AgeVariableFactory()
    var_var = VariableFactory(domain__code="FOO", domain__label="foo")
    qual_var = QualifierVariableFactory(domain__code="BAR", domain__label="bar")
    study_1 = StudyFactory()
    study_2 = StudyFactory()
    CountFactory(codes=[var_var], study=study_2, count=21)
    CountFactory(codes=[age_var, var_var], study=study_1, count=22)
    CountFactory(codes=[age_var, var_var, qual_var], study=study_1, count=23)

    studies = Study.objects.all()

    df = get_counts_df(studies=studies)

    #    id  study study_label  count domain_code domain_label  codes
    # 0   1      2        ID#1     21         FOO          foo      2
    # 1   2      1        ID#0     22      AGECAT          Age      1
    # 2   2      1        ID#0     22         FOO          foo      2
    # 3   3      1        ID#0     23      AGECAT          Age      1
    # 4   3      1        ID#0     23         FOO          foo      2
    # 5   3      1        ID#0     23         BAR          bar      3

    assert set(df.columns) == set(['id', 'study', 'study_label', 'count', 'domain_code', 'domain_label', 'codes', 'subjects'])
    assert len(df) == 6


@pytest.mark.django_db
def test_get_counts_df_no_counts_for_studies():
    StudyFactory.create_batch(2)

    studies = Study.objects.all()

    df = get_counts_df(studies=studies)

    #    id  study study_label  count domain_code domain_label  codes

    assert set(df.columns) == set(['id', 'study', 'study_label', 'count', 'domain_code', 'domain_label', 'codes', 'subjects'])
    assert len(df) == 0


@pytest.fixture
@pytest.mark.django_db
def test_df():
    age_var = AgeVariableFactory(label='age')
    var_var = VariableFactory(domain__code="FOO", domain__label="foo", label="var")
    qual_var = QualifierVariableFactory(domain__code="BAR", domain__label="bar")
    study_1 = StudyFactory()
    study_2 = StudyFactory()
    CountFactory(codes=[var_var], study=study_2, count=21)
    CountFactory(codes=[age_var, var_var], study=study_1, count=22)
    CountFactory(codes=[age_var, var_var, qual_var], study=study_1, count=23)

    df = get_counts_df(studies=Study.objects.all())
    return df


@pytest.fixture
def pivot_df(test_df):
    return pivot_counts_df(test_df)


@pytest.mark.django_db
def test_get_counts_by_domain(test_df):
    df = get_counts_by_domain(test_df)

    #    study study_label domain_code  count domain_label
    # 0      5        ID#4      AGECAT     45          Age
    # 1      5        ID#4         BAR     23          bar
    # 2      5        ID#4         FOO     45          foo
    # 3      6        ID#5         FOO     21          foo

    assert set(df.columns) == set(['study', 'study_label', 'domain_code', 'count', 'domain_label', 'subjects'])
    pd.util.testing.assert_series_equal(df['count'],
                                        pd.Series(data=[23, 23, 23, 21], name='count'))
    pd.util.testing.assert_series_equal(df['domain_label'],
                                        pd.Series(data=["Age", "bar", "foo", "foo"], name='domain_label'))


@pytest.mark.django_db
def test_pivot_counts_df(test_df):
    df = pivot_counts_df(test_df)

    # domain_code                 AGECAT  BAR  FOO
    # id study study_label count
    # 7  8     ID#7        21        NaN  NaN  8.0
    # 8  7     ID#6        22        7.0  NaN  8.0
    # 9  7     ID#6        23        7.0  9.0  8.0

    assert len(df) == 3
    pd.util.testing.assert_index_equal(df.columns,
                                       pd.Index(['AGECAT', 'BAR', 'FOO'], dtype='object', name='domain_code'))


@pytest.mark.django_db
def test_get_variable_counts(pivot_df):
    # implementation detail to avoid repeating query
    variables = Variable.objects.all()
    var_lookup = groupby('id', variables.values('id', 'label', 'code'))
    df = get_variable_counts(pivot_df, var_lookup, "FOO")

    #    study study_label   FOO  id  count  var_code   var_label
    # 0      9        ID#8  11.0  23     45      11.0         var
    # 1     10        ID#9  11.0  10     21      11.0         var

    assert set(df.columns) == set(['study', 'study_label', 'FOO', 'id', 'count', 'var_code', 'var_label', 'subjects'])
    pd.util.testing.assert_series_equal(df.var_label, pd.Series(data=["var", "var"], name='var_label'))


@pytest.mark.django_db
def test_get_variable_counts_domain_not_in_df(pivot_df):
    # implementation detail to avoid repeating query
    variables = Variable.objects.all()
    var_lookup = groupby('id', variables.values('id', 'label', 'code'))
    df = get_variable_counts(pivot_df, var_lookup, "FAKEDOMAIN")

    assert df is None


@pytest.mark.django_db
def test_get_variable_count_by_variable(pivot_df):
    # implementation detail to avoid repeating query
    variables = Variable.objects.all()
    var_lookup = groupby('id', variables.values('id', 'label', 'code'))
    df = get_variable_count_by_variable(pivot_df, var_lookup, "FOO", qualifier_code="AGECAT")

    # domain_code  study study_label  AGECAT   FOO  id  count  var_code var_label  domain_code  qual_code  qual_label
    # 0               11       ID#10    13.0  14.0  29     45      14.0       var  0                 13.0         age

    assert set(df.columns) == set(['study', 'study_label', 'AGECAT', 'FOO', 'id', 'count', 'var_code', 'var_label', 'qual_code', 'qual_label', 'subjects'])
    pd.util.testing.assert_series_equal(df.var_label, pd.Series(data=["var"], name='var_label'))
    pd.util.testing.assert_series_equal(df.qual_label, pd.Series(data=["age"], name='qual_label'))


@pytest.mark.django_db
def test_get_variable_count_by_variable_qualifier_domain_not_in_df(pivot_df):
    # implementation detail to avoid repeating query
    variables = Variable.objects.all()
    var_lookup = groupby('id', variables.values('id', 'label', 'code'))
    df = get_variable_count_by_variable(pivot_df, var_lookup, "FOO", qualifier_code="FAKEDOMAIN")

    assert df is None
