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

import os

import pytest
import pandas as pd
from django.core.management import call_command
from django.core.management.base import CommandError

from ..management.commands import load_idx
from ..management.commands.load_idx import (
    get_qualifiers, get_study,
    get_valid_qualifiers, get_domain_variable
)
from ..models import Study, Variable, Count

from .factories import (
    SampleDomainFactory as DomainFactory,
    StudyFactory,
)


@pytest.fixture
def command_kwargs():
    return dict(study_id_field="STUDYID",
                count_subj_field="COUNT_SUBJ",
                count_obs_field="COUNT_OBS")

@pytest.mark.django_db()
def test_get_study_existing(command_kwargs):
    study = StudyFactory()
    row = pd.Series(dict(STUDYID=study.study_id))
    assert get_study(row, **command_kwargs) == study


@pytest.mark.django_db()
def test_get_study_create_new(command_kwargs):
    row = pd.Series(dict(STUDYID='TEST'))
    assert get_study(row, **command_kwargs).study_id == 'TEST'


@pytest.mark.django_db()
def test_get_study_empty_study_name(command_kwargs):
    row = pd.Series(dict(STUDYID=None))
    assert get_study(row, **command_kwargs) is None


@pytest.mark.django_db()
def test_get_domain_variable_simple():
    domain = DomainFactory()
    row = pd.Series(dict(SAMPLETEST='Test', SAMPLETESTCD='A'))
    variable = get_domain_variable(row, domain)
    assert variable.code == row['SAMPLETESTCD']
    assert variable.label == row['SAMPLETEST']


@pytest.mark.django_db()
def test_get_domain_variable_with_category():
    domain = DomainFactory()
    row = pd.Series(dict(SAMPLETEST='Test', SAMPLETESTCD='A', SAMPLECAT='Cat'))
    variable = get_domain_variable(row, domain)
    assert variable.code == row['SAMPLETESTCD']
    assert variable.label == row['SAMPLETEST']
    assert variable.category == row['SAMPLECAT']


@pytest.mark.django_db()
def test_get_domain_variable_with_empty_code():
    domain = DomainFactory()
    row = pd.Series(dict(SAMPLETEST='Test', SAMPLETESTCD=None, SAMPLECAT='Cat'))
    variable = get_domain_variable(row, domain)
    assert variable is None


@pytest.mark.django_db()
def test_get_valid_qualifiers_single():
    domain1 = DomainFactory(is_qualifier=True)
    DomainFactory(is_qualifier=True, code='A')
    columns = ['SAMPLE', 'SAMPLEN', 'INVALID', 'INVALIDN']
    qualifiers = get_valid_qualifiers(columns)
    assert qualifiers == [(domain1, 'SAMPLE', 'N')]


@pytest.mark.django_db()
def test_get_valid_qualifiers_multiple():
    domain1 = DomainFactory(is_qualifier=True)
    domain2 = DomainFactory(is_qualifier=True, code='A')
    DomainFactory(is_qualifier=True, code='B')
    columns = ['SAMPLE', 'SAMPLEN', 'A', 'AN', 'INVALID', 'INVALIDN']
    qualifiers = get_valid_qualifiers(columns)
    assert qualifiers == [(domain1, 'SAMPLE', 'N'),
                          (domain2, 'A', 'N')]


@pytest.mark.django_db()
def test_get_valid_qualifiers_with_wildcard():
    domain1 = DomainFactory(is_qualifier=True, code='*SPEC')
    DomainFactory(is_qualifier=True, code='A')
    columns = ['TESTSPEC', 'TESTSPECN', 'INVALID', 'INVALIDN']
    qualifiers = get_valid_qualifiers(columns)
    assert qualifiers == [(domain1, 'TESTSPEC', 'N')]


@pytest.mark.django_db()
def test_get_valid_qualifiers_with_wildcard_clash():
    DomainFactory(is_qualifier=True, code='*SPEC')
    with pytest.raises(Exception, match='Qualifier code must match only one column per file.'):
        get_valid_qualifiers(['TESTSPEC', 'TESTSPECN',
                              'TEST2SPEC', 'TEST2SPECN'])


@pytest.mark.django_db()
def test_get_qualifiers_single():
    domain1 = DomainFactory(is_qualifier=True)
    DomainFactory(is_qualifier=True, code='A')

    # Declare data with one registered and one ignored qualifier
    row = pd.Series(dict(SAMPLE='Sample label', SAMPLEN=2,
                         TEST='A', TESTN='0'))
    valid_qualifiers = [(domain1, domain1.code, 'N')]

    qualifiers = get_qualifiers(row, valid_qualifiers)
    assert len(qualifiers) == 1
    assert qualifiers[0].domain == domain1
    assert qualifiers[0].code == '2'
    assert qualifiers[0].label == 'Sample label'


@pytest.mark.django_db()
def test_get_qualifiers_multiple():
    domain1 = DomainFactory(is_qualifier=True)
    domain2 = DomainFactory(is_qualifier=True, code='A')
    DomainFactory(is_qualifier=True, code='TEST')

    # Declare data with two registered and one ignored qualifier
    row = pd.Series(dict(SAMPLE='Sample label', SAMPLEN='2',
                         TEST='Test label', TESTN='0', A='A label', AN='1'))
    valid_qualifiers = [(domain1, domain1.code, 'N'),
                        (domain2, domain2.code, 'N')]

    qualifiers = get_qualifiers(row, valid_qualifiers)
    assert len(qualifiers) == 2
    assert qualifiers[0].domain == domain1
    assert qualifiers[0].code == '2'
    assert qualifiers[0].label == 'Sample label'
    assert qualifiers[1].domain == domain2
    assert qualifiers[1].code == '1'
    assert qualifiers[1].label == 'A label'


@pytest.mark.django_db()
def test_get_qualifiers_undefined_raises_exception():
    domain1 = DomainFactory(is_qualifier=True)
    DomainFactory(is_qualifier=True, code='A')

    # Declare data with an empty code
    row = pd.Series(dict(SAMPLE='Sample label', SAMPLEN=None,
                         TEST='A', TESTN='0'))
    valid_qualifiers = [(domain1, domain1.code, 'N')]

    with pytest.raises(ValueError, match='Qualifiers cannot be empty'):
        get_qualifiers(row, valid_qualifiers)


@pytest.mark.django_db()
def test_get_qualifiers_with_wildcard_code():
    domain1 = DomainFactory(is_qualifier=True, code='*SAMPLE')
    DomainFactory(is_qualifier=True, code='A')

    # Declare data with one registered and one ignored qualifier
    row = pd.Series(dict(TESTSAMPLE='Sample label', TESTSAMPLEN=2,
                         TEST='A', TESTN='0'))
    valid_qualifiers = [(domain1, 'TESTSAMPLE', 'N')]

    qualifiers = get_qualifiers(row, valid_qualifiers)
    assert len(qualifiers) == 1
    assert qualifiers[0].domain == domain1
    assert qualifiers[0].code == '2'
    assert qualifiers[0].label == 'Sample label'


def _create_sample_idx_df():
    study_ids = ['test%d' % i for i in range(10)]
    test = [str(i) for i in range(10)]
    testn = range(10)
    counts = range(0, 20, 2)
    df = pd.DataFrame({'STUDYID': study_ids, 'SAMPLETEST': test,
                       'SAMPLETESTCD': testn, 'COUNT_SUBJ': counts,
                       'COUNT_OBS': counts})
    return df


@pytest.mark.django_db()
def test_process_idx_simple(command_kwargs):
    df = _create_sample_idx_df()
    domain = DomainFactory()

    # Load data and check counts were associated with correct
    # variables and studies
    load_idx.process_idx_df(df, domain=domain, **command_kwargs)
    assert Study.objects.count() == 10
    assert Count.objects.count() == 10
    assert Variable.objects.count() == 10
    model_iter = zip(Count.objects.all(), Variable.objects.all(), Study.objects.all())
    for count, variable, study in model_iter:
        assert list(count.codes.all()) == [variable]
        assert count.study == study


@pytest.mark.django_db()
def test_load_idx_with_repeated_studyid(command_kwargs):
    # Create data with repeated study ids
    df = _create_sample_idx_df()
    df['STUDYID'] = 'test1'

    # Ensure only one Study was created
    domain = DomainFactory()
    load_idx.process_idx_df(df, domain=domain, **command_kwargs)
    assert Study.objects.count() == 1
    assert Count.objects.count() == 10
    assert Variable.objects.count() == 10
    study = Study.objects.first()
    for query in Count.objects.all():
        assert query.study == study


@pytest.mark.django_db()
def test_load_idx_with_repeated_domain_variable(command_kwargs):
    # Create data with repeated domain variables
    df = _create_sample_idx_df()
    df['SAMPLETEST'] = '1'
    df['SAMPLETESTCD'] = 1

    # Ensure only one variable was created
    domain = DomainFactory()
    load_idx.process_idx_df(df, domain=domain, **command_kwargs)
    assert Study.objects.count() == 10
    assert Count.objects.count() == 10
    assert Variable.objects.count() == 1
    code = Variable.objects.first()
    for query in Count.objects.all():
        codes = query.codes.all()
        assert len(codes) == 1
        assert code in codes


@pytest.mark.django_db()
def test_load_idx_skip_rows_with_invalid_observation_count(command_kwargs):
    # Create data with invalid observation counts
    df = _create_sample_idx_df()
    df['COUNT_OBS'][0:5] = None

    # Ensure only rows with valid counts were processed
    domain = DomainFactory()
    load_idx.process_idx_df(df, domain=domain, **command_kwargs)
    assert Study.objects.count() == 5
    assert Count.objects.count() == 5
    assert Variable.objects.count() == 5


@pytest.mark.django_db()
def test_load_idx_skip_rows_with_invalid_subject_count(command_kwargs):
    # Create data with invalid subject counts
    df = _create_sample_idx_df()
    df['COUNT_SUBJ'][0:5] = None

    # Ensure only rows with valid counts were processed
    domain = DomainFactory()
    load_idx.process_idx_df(df, domain=domain, **command_kwargs)
    assert Study.objects.count() == 5
    assert Count.objects.count() == 5
    assert Variable.objects.count() == 5


@pytest.mark.django_db()
def test_load_idx_skip_on_missing_studyid_column(command_kwargs):
    # Create dataframe with missing STUDYID column
    deleted = 'STUDYID'
    df = _create_sample_idx_df()
    del df[deleted]

    msg = 'IDX file does not contain %s column, skipping.' % deleted
    with pytest.raises(ValueError, match=msg):
        domain = DomainFactory()
        load_idx.process_idx_df(df, domain=domain, **command_kwargs)


@pytest.mark.django_db()
def test_load_idx_skip_on_missing_count_subj_column(command_kwargs):
    # Create dataframe with missing COUNT_SUBJ column
    deleted = 'COUNT_SUBJ'
    df = _create_sample_idx_df()
    del df[deleted]

    msg = 'IDX file does not contain %s column, skipping.' % deleted
    with pytest.raises(ValueError, match=msg):
        domain = DomainFactory()
        load_idx.process_idx_df(df, domain=domain, **command_kwargs)


@pytest.mark.django_db()
def test_load_idx_skip_on_missing_count_obs_column(command_kwargs):
    # Create dataframe with missing COUNT_OBS column
    deleted = 'COUNT_OBS'
    df = _create_sample_idx_df()
    del df[deleted]

    msg = 'IDX file does not contain %s column, skipping.' % deleted
    with pytest.raises(ValueError, match=msg):
        domain = DomainFactory()
        load_idx.process_idx_df(df, domain=domain, **command_kwargs)


@pytest.mark.django_db()
def test_load_idx_command_codes(command_kwargs):
    """Test load_idx command can read CSV file"""
    DomainFactory()
    file_path = os.path.dirname(os.path.abspath(__file__))
    sample_csv = os.path.join(file_path, 'IDX_SAMPLE.csv')
    call_command('load_idx', sample_csv, **command_kwargs)
    assert Study.objects.count() == 1
    assert Variable.objects.count() == 18
    assert Count.objects.count() == 18


@pytest.mark.django_db()
def test_load_idx_command_qualifiers(command_kwargs):
    """Test load_idx command can read qualifiers from CSV file"""
    DomainFactory(code='RELTIVE', is_qualifier=True)
    DomainFactory()
    file_path = os.path.dirname(os.path.abspath(__file__))
    sample_csv = os.path.join(file_path, 'IDX_SAMPLE.csv')
    call_command('load_idx', sample_csv, **command_kwargs)
    assert Study.objects.count() == 1
    assert Variable.objects.count() == 20
    assert Count.objects.count() == 18


@pytest.mark.django_db()
def test_load_idx_nonexistent_file():
    """Test load_idx command fails as expected on non-existent file."""
    with pytest.raises(CommandError):
        call_command('load_idx', './fake_file')
