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

from django import forms
from django.core.management import call_command
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic.edit import FormView


class ImportStudiesForm(forms.Form):
    study_id_field = forms.CharField(max_length=50,
                                     label='Name of column to use as Study ID',
                                     initial='STUDYID')
    studies_file = forms.FileField(label='Select studies CSV file')
    keep_fields = forms.BooleanField(required=False, initial=False,
                                     label='Clear data but keep study fields')


class ImportStudiesView(PermissionRequiredMixin, FormView):
    permission_required = 'studies.create_study'
    template_name = "studies/admin/import_studies.html"
    form_class = ImportStudiesForm

    def get_success_url(self):
        return reverse('admin:studies_studyfield_changelist')

    def get_context_data(self, **kwargs):
        context = super(ImportStudiesView, self).get_context_data(**kwargs)
        context.update(dict(has_permission=True))
        return context

    def form_valid(self, form):
        uploaded_file = form.files['studies_file']
        study_id_field = form['study_id_field'].value()
        keep_fields = form['keep_fields'].value()
        call_command('load_studies', uploaded_file.temporary_file_path(),
                     study_id_field=study_id_field, keep_fields=keep_fields)
        return super(ImportStudiesView, self).form_valid(form)


class ImportIDXForm(forms.Form):
    study_id_field = forms.CharField(max_length=50,
                                     label='Name of column to use as Study ID',
                                     initial='STUDYID')
    count_subj_field = forms.CharField(max_length=50,
                                       label='Name of column to use as Subject Count',
                                       initial='COUNT_SUBJ')
    count_obs_field = forms.CharField(max_length=50,
                                      label='Name of column to use as Observation Count',
                                      initial='COUNT_OBS')
    idx_file = forms.FileField(label='Select zip of IDX files')


class ImportIDXView(PermissionRequiredMixin, FormView):
    permission_required = 'studies.create_count'
    template_name = "studies/admin/import_idx_files.html"
    form_class = ImportIDXForm

    def get_success_url(self):
        return reverse('admin:studies_count_changelist')

    def get_context_data(self, **kwargs):
        context = super(ImportIDXView, self).get_context_data(**kwargs)
        context.update(dict(has_permission=True))
        return context

    def form_valid(self, form):
        uploaded_file = form.files['idx_file']
        study_id_field = form['study_id_field'].value()
        count_subj_field = form['count_subj_field'].value()
        count_obs_field = form['count_obs_field'].value()
        call_command('load_idx',
                     uploaded_file.temporary_file_path(),
                     study_id_field=study_id_field,
                     count_subj_field=count_subj_field,
                     count_obs_field=count_obs_field)
        return super(ImportIDXView, self).form_valid(form)
