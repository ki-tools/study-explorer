import os
import zipfile
import tempfile

import pytest
from django.core.files.uploadedfile import File
from django.urls import reverse
from django.core.management.base import CommandError

from ..admin import IsVisibleListFilter, StudyFieldAdmin
from ..admin_views import ImportStudiesForm, ImportIDXForm
from ..models import StudyField, Study, StudyVariable, Variable, Count, Domain

from .factories import StudyFieldFactory


@pytest.mark.parametrize("display,cnt", [
    ('lil_order', 6),
    ('big_order', 8),
    ('either', 9),
    ('both', 5),
])
@pytest.mark.django_db
def test_study_field_admin_is_visible_list_filter(display, cnt):
    StudyFieldFactory.create_batch(2)
    StudyFieldFactory.create_batch(3, big_order=1)
    StudyFieldFactory.create_batch(1, lil_order=3)
    StudyFieldFactory.create_batch(5, lil_order=2, big_order=7)

    filt = IsVisibleListFilter(None,
                               {'display': display},
                               StudyField,
                               StudyFieldAdmin)
    qs = filt.queryset(None, StudyField.objects.all())
    assert qs.count() == cnt


def test_importstudiesform_valid():
    filename = 'studies_sample.csv'
    file_path = os.path.dirname(os.path.abspath(__file__))
    sample_csv = os.path.join(file_path, filename)
    with open(sample_csv, 'rb') as f:
        tmp_file = File(f)
        files = dict(studies_file=tmp_file)
        data = dict(study_id_field="Study_ID")
        form = ImportStudiesForm(files=files, data=data)
        assert form.is_valid()


def test_importidxform_valid():
    filename = 'IDX_SAMPLE.csv'
    file_path = os.path.dirname(os.path.abspath(__file__))
    sample_csv = os.path.join(file_path, filename)
    with tempfile.NamedTemporaryFile(suffix='zip') as tmp:
        with zipfile.ZipFile(tmp, 'w') as archive:
            with open(sample_csv, 'rb') as f:
                archive.writestr(filename, f.read())
        tmp.seek(0)
        tmp_file = File(tmp)
        data = dict(study_id_field="Study_ID",
                    count_subj_field="COUNT_SUBJ",
                    count_obs_field="COUNT_OBS")
        form = ImportIDXForm(files=dict(idx_file=tmp_file), data=data)
        assert form.is_valid()


@pytest.mark.django_db()
def test_import_studies_response(admin_client):
    response = admin_client.get('/admin/studies/study/import_studies/')
    assert response.status_code == 200


@pytest.mark.django_db()
def test_import_idx_response(admin_client):
    response = admin_client.get('/admin/studies/count/import_idx/')
    assert response.status_code == 200


@pytest.mark.django_db()
def test_admin_upload_idx_zip(admin_client):
    filename = 'IDX_SAMPLE.csv'
    file_path = os.path.dirname(os.path.abspath(__file__))
    sample_csv = os.path.join(file_path, filename)

    Domain.objects.create(code='RELTIVE', is_qualifier=True)
    Domain.objects.create(code='SAMPLE')

    with tempfile.NamedTemporaryFile(suffix='zip') as tmp:
        with zipfile.ZipFile(tmp, 'w') as archive:
            with open(sample_csv, 'rb') as f:
                archive.writestr(filename, f.read())
        tmp.seek(0)
        tmp_file = File(tmp)
        response = admin_client.post('/admin/studies/count/import_idx/',
                                     {'idx_file': tmp_file,
                                      'study_id_field': "STUDYID",
                                      'count_subj_field': "COUNT_SUBJ",
                                      'count_obs_field': "COUNT_OBS"})
    assert response.status_code == 302
    assert response.url == reverse('admin:studies_count_changelist')

    assert len(Study.objects.all()) == 1
    assert len(Variable.objects.all()) == 20
    assert len(Count.objects.all()) == 18


@pytest.mark.django_db()
def test_admin_upload_studies_clear_all(admin_client):
    filename = 'studies_sample.csv'
    file_path = os.path.dirname(os.path.abspath(__file__))
    sample_csv = os.path.join(file_path, filename)

    with open(sample_csv, 'rb') as f:
        tmp_file = File(f)
        response = admin_client.post('/admin/studies/study/import_studies/',
                                     {'studies_file': tmp_file, 'study_id_field': 'STUDYID'})
    assert response.status_code == 302
    assert response.url == reverse('admin:studies_studyfield_changelist')

    assert len(Study.objects.all()) == 9
    assert StudyField.objects.count() == 47
    assert StudyVariable.objects.count() == 114
    counts = (StudyVariable.objects
                           .filter(study_field__field_name='Subject_Count')
                           .values_list('value', flat=True))
    assert sum([float(c) for c in counts if c is not None]) == 708147


@pytest.mark.django_db()
def test_admin_upload_studies_keep_study_fields(admin_client):
    filename = 'studies_sample_alt.csv'
    file_path = os.path.dirname(os.path.abspath(__file__))
    sample_csv = os.path.join(file_path, filename)

    with open(sample_csv, 'rb') as f:
        tmp_file = File(f)
        response = admin_client.post('/admin/studies/study/import_studies/',
                                     {'studies_file': tmp_file, 'study_id_field': 'STUDYID'})
    assert response.status_code == 302
    assert response.url == reverse('admin:studies_studyfield_changelist')

    filename = 'studies_sample.csv'
    file_path = os.path.dirname(os.path.abspath(__file__))
    sample_csv = os.path.join(file_path, filename)

    with open(sample_csv, 'rb') as f:
        tmp_file = File(f)
        response = admin_client.post('/admin/studies/study/import_studies/',
                                     {'studies_file': tmp_file, 'study_id_field': 'STUDYID', 'keep_fields': True})
    assert response.status_code == 302
    assert response.url == reverse('admin:studies_studyfield_changelist')

    assert len(Study.objects.all()) == 9
    assert StudyField.objects.count() == 48
    assert StudyVariable.objects.count() == 114


@pytest.mark.django_db()
def test_admin_upload_studies_study_id_field_not_in_files(admin_client):
    filename = 'studies_sample_alt.csv'
    file_path = os.path.dirname(os.path.abspath(__file__))
    sample_csv = os.path.join(file_path, filename)
    study_info_field = 'FOOBAR'

    with open(sample_csv, 'rb') as f:
        tmp_file = File(f)
        msg = ('Please ensure that FOOBAR is a column header in '
               'uploaded file')
        with pytest.raises(CommandError) as excinfo:
            admin_client.post('/admin/studies/study/import_studies/',
                              {'studies_file': tmp_file,
                               'study_id_field': study_info_field})
    assert str(excinfo.value) == msg
