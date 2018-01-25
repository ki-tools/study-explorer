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
from django.db.models import Q
from django.forms import ValidationError

from ..management.commands import load_studies
from ..models import StudyField, Study, StudyVariable
from .factories import StudyFieldFactory

FILE_PATH = os.path.dirname(__file__)
SAMPLE_FILE = os.path.join(FILE_PATH, 'studies_sample.csv')
SAMPLE_FILE_UTF = os.path.join(FILE_PATH, 'studies_sample_utf.csv')
ALT_FILE = os.path.join(FILE_PATH, 'studies_sample_alt.csv')


@pytest.fixture
def df_of_studies():
    return pd.read_csv(SAMPLE_FILE,
                       index_col='STUDYID',
                       na_values=load_studies.EMPTY_IDENTIFIERS)


@pytest.fixture
def load_sample_studies(df_of_studies, transactional_db):
    load_studies.Command.process_studies(df_of_studies)


def test_process_studies(load_sample_studies):
    assert Study.objects.count() == 9
    assert StudyField.objects.count() == 47
    assert StudyVariable.objects.count() == 114


def test_process_studies_utf(transactional_db):
    df = pd.read_csv(SAMPLE_FILE_UTF,
                     index_col='STUDYID',
                     na_values=load_studies.EMPTY_IDENTIFIERS)
    load_studies.Command.process_studies(df)

    assert Study.objects.count() == 9
    assert StudyField.objects.count() == 47
    # TODO: why isn't this 186?
    assert StudyVariable.objects.count() == 115


def test_process_studies_alt(transactional_db):
    df = pd.read_csv(ALT_FILE,
                     index_col='STUDYID',
                     na_values=load_studies.EMPTY_IDENTIFIERS)
    load_studies.Command.process_studies(df)

    assert Study.objects.count() == 1
    assert StudyField.objects.count() == 48
    additional_program_folder = list(StudyVariable.objects
                                     .filter(study_field__field_name='PROGRAM_FOLDER.1')
                                     .values_list('value', flat=True))
    assert additional_program_folder == ['WHAT']


def test_process_studies_loads_all_columns(df_of_studies, load_sample_studies):
    expected = list(df_of_studies.columns)
    actual = list(StudyField.objects.values_list('field_name', flat=True))
    assert actual == expected


def test_process_studies_subject_count(load_sample_studies):
    counts = StudyVariable.objects.\
        filter(study_field__field_name='Subject_Count').\
        values_list('value', flat=True)
    assert sum([float(c) for c in counts if c is not None]) == 708147


def test_process_studies_study_id_field_not_in_file(transactional_db):
    with pytest.raises(CommandError) as excinfo:
        call_command('load_studies', SAMPLE_FILE, study_id_field='FOOBAR')
    msg = ('Please ensure that FOOBAR is a column header in '
           'uploaded file')
    assert str(excinfo.value) == msg


def test_load_studies_command(transactional_db):
    " Test my custom command."
    call_command('load_studies', SAMPLE_FILE)
    assert Study.objects.count() == 9
    assert StudyField.objects.count() == 47
    assert StudyVariable.objects.count() == 114


def test_load_studies_command_utf(transactional_db):
    " Test my custom command."
    call_command('load_studies', SAMPLE_FILE_UTF)
    assert Study.objects.count() == 9


def test_load_studies_nonexistent_file(transactional_db):
    " Test my custom command."
    with pytest.raises(CommandError) as excinfo:
        call_command('load_studies', './fake_file')
    msg = './fake_file is not a valid path.'
    assert str(excinfo.value) == msg


def test_load_studies_file_is_not_a_csv_raises_error(transactional_db):
    " Test my custom command."
    with pytest.raises(CommandError) as excinfo:
        call_command('load_studies', os.path.join(FILE_PATH, 'test_views.py'))
    msg = 'Please ensure your upload is a valid csv file.'
    assert str(excinfo.value) == msg


def test_load_studies_command_clear_all(transactional_db, df_of_studies):
    call_command('load_studies', ALT_FILE)
    additional_fields = list(StudyField.objects
                                       .filter(~Q(field_name__in=df_of_studies.columns))
                                       .values_list('studyvariable__value', flat=True))
    assert additional_fields == ['WHAT']
    assert Study.objects.all().count() == 1
    assert StudyVariable.objects.all().count() == 27

    call_command('load_studies', SAMPLE_FILE)
    additional_fields = StudyField.objects.filter(~Q(field_name__in=df_of_studies.columns))
    assert additional_fields.count() == 0
    assert Study.objects.all().count() == 9
    assert StudyVariable.objects.all().count() == 114


def test_load_studies_command_clear_studies_and_variables_but_keep_fields(transactional_db, df_of_studies):
    call_command('load_studies', ALT_FILE)
    call_command('load_studies', SAMPLE_FILE, keep_fields=True)
    additional_fields = StudyField.objects.filter(~Q(field_name__in=df_of_studies.columns))
    assert additional_fields.count() == 1
    assert Study.objects.all().count() == 9
    assert StudyVariable.objects.all().count() == 114


def test_load_studies_command_keep_studies_and_variables_and_fields(transactional_db, df_of_studies):
    call_command('load_studies', ALT_FILE)
    call_command('load_studies', SAMPLE_FILE, clear=False)
    additional_fields = StudyField.objects.filter(~Q(field_name__in=df_of_studies.columns))
    assert additional_fields.count() == 1
    assert Study.objects.all().count() == 10
    assert StudyVariable.objects.all().count() == 121


def test_load_studies_command_clear_studies_and_variables_but_keep_int_field_types(transactional_db):
    StudyFieldFactory(field_name='Start_Year', field_type='int')
    call_command('load_studies', ALT_FILE, keep_fields=True)
    assert StudyField.objects.filter(field_name='Start_Year').first().field_type == 'int'


def test_load_studies_command_clear_studies_and_variables_but_keep_int_field_types_raises_error(transactional_db):
    StudyFieldFactory(field_name='Country', field_type='int')
    with pytest.raises(ValidationError) as excinfo:
        call_command('load_studies', ALT_FILE, keep_fields=True)
    msg = 'Country: USA cannot be cast to Integer type'
    assert excinfo.value.message == msg


def test_load_studies_command_clear_studies_and_variables_but_keep_list_field_types(transactional_db):
    StudyFieldFactory(field_name='Country', field_type='list')
    call_command('load_studies', ALT_FILE, keep_fields=True)
    assert StudyField.objects.filter(field_name='Country').first().field_type == 'list'
    actual = list(StudyVariable.objects.filter(study_field__field_name='Country')
                                       .values_list('value', flat=True))
    assert actual == ['USA']


def test_load_studies_command_clear_all_overwrites_study_field_settings(transactional_db):
    StudyFieldFactory(field_name='Country', field_type='int')
    call_command('load_studies', ALT_FILE)
    assert StudyField.objects.filter(field_name='Country').first().field_type == 'str'
    actual = list(StudyVariable.objects.filter(study_field__field_name='Country')
                                       .values_list('value', flat=True))
    assert actual == ['USA']
