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

from pandas import read_csv, read_excel, notnull
from django.core.management.base import BaseCommand, CommandError

from ...models import StudyField, Study, StudyVariable, EMPTY_IDENTIFIERS, Filter, Domain

ENCODINGS = ['latin-1', 'utf-8']


class Command(BaseCommand):
    help = 'Loads the StudyInfo Excel or CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str)
        parser.add_argument('-study_id_field', type=str, default='STUDYID',
                            help='Name of column to use as study_id.')
        parser.add_argument('--clear', action='store_true',
                            default=True, dest='clear',
                            help='Clear studies before processing data.')
        parser.add_argument('--keep_fields', action='store_true',
                            default=False, dest='keep_fields',
                            help='Do not clear study fields before processing data.')

    def handle(self, *args, **options):
        existing_filters = []
        for f in Filter.objects.all():
            existing_filters.append({
                'domain_code': f.domain.code if f.domain else None,
                'study_field_name': f.study_field.field_name if f.study_field else None,
                'label': f.label,
                'widget': f.widget,
                'widget_json': f.widget_json
            })

        if options['clear']:

            study_variables = StudyVariable.objects.all()
            self.stdout.write('Deleting %s study variables' % len(study_variables))
            study_variables.delete()

            studies = Study.objects.all()
            self.stdout.write('Deleting %s studies' % len(studies))
            studies.delete()

            if not options['keep_fields']:

                study_fields = StudyField.objects.all()
                self.stdout.write('Deleting %s study fields' % len(study_fields))
                study_fields.delete()

        n_studies = Study.objects.count()
        n_study_fields = StudyField.objects.count()
        n_study_variables = StudyVariable.objects.count()

        if not os.path.isfile(options['file']):
            raise CommandError('%s is not a valid path.' % options['file'])

        study_info = None
        msg = ''
        study_id_field = options['study_id_field']
        kwargs = dict(na_values=EMPTY_IDENTIFIERS)
        for encoding in ENCODINGS:
            try:
                if options['file'].endswith('csv'):

                    msg = 'File could not be opened ensure it is a valid csv file.'
                    study_info = read_csv(options['file'],
                                          encoding=encoding, **kwargs)
                elif options['file'].endswith(('xls', 'xlsx')):
                    msg = 'File could not be opened ensure it is a valid Excel file.'
                    study_info = read_excel(options['file'],
                                            encoding=encoding, **kwargs)
                else:
                    # Otherwise - assume it's a csv
                    msg = 'Please ensure your upload is a valid csv file.'
                    study_info = read_csv(options['file'],
                                          encoding=encoding, **kwargs)
            except:
                continue
        if study_info is None:
            raise CommandError(msg)

        try:
            study_info = study_info.set_index(study_id_field)
        except:
            msg = ('Please ensure that {0} is a column header in '
                   'uploaded file'.format(study_id_field))
            raise CommandError(msg)

        self.process_studies(study_info)

        if options['keep_fields'] or not options['clear']:
            for study_field in StudyField.objects.all():
                try:
                    study_field.clean()
                except:
                    for study_variable in StudyVariable.objects.filter(study_field=study_field):
                        study_variable.clean()

        for filter in existing_filters:
            label = label = filter['label']
            domain_code = filter['domain_code']
            study_field_name = filter['study_field_name']
            domain = None
            study_field = None

            if domain_code:
                domain = Domain.objects.filter(code=domain_code).first()
                if not domain:
                    self.stdout.write('Cannot recreate filter, domain not found: {0}'.format(domain_code))
                    continue

            if study_field_name:
                study_field = StudyField.objects.filter(field_name=study_field_name).first()
                if not study_field:
                    self.stdout.write('Cannot recreate filter, study_field not found: {0}'.format(study_field_name))
                    continue

            existing_filter = Filter.objects.filter(domain=domain, study_field=study_field, label=label).first()
            if not existing_filter:
                new_filter = Filter(
                    domain=domain,
                    study_field=study_field,
                    label=label,
                    widget=filter['widget'],
                    widget_json=filter['widget_json']
                )
                new_filter.save()
                self.stdout.write('Recreated filter: Domain: {0}, Study Field: {1}, Label: {2}'.format(
                    getattr(new_filter.domain, 'code', 'None'),
                    getattr(new_filter.study_field, 'label', 'None'),
                    new_filter.label
                ))
            else:
                self.stdout.write('Filter exists: Domain: {0}, Study Field: {1}, Label: {2}'.format(
                    getattr(existing_filter.domain, 'code', 'None'),
                    getattr(existing_filter.study_field, 'label', 'None'),
                    existing_filter.label
                ))

        self.stdout.write('Added %s Study Field entries' %
                          (StudyField.objects.count() - n_study_fields))
        self.stdout.write('Added %s Study entries' %
                          (Study.objects.count() - n_studies))
        self.stdout.write('Added %s Study Variable entries' %
                          (StudyVariable.objects.count() - n_study_variables))

    @classmethod
    def process_studies(self, df):
        df = df[notnull(df.index)]
        df = df.where((notnull(df)), None)

        for field_name in df.columns:
            field_type = 'str'
            study_field_name = field_name
            set_field_type = False
            if '::' in field_name:
                study_field_name, field_type = field_name.split('::', maxsplit=1)
                set_field_type = True
            study_field_name = study_field_name.upper()
            field_type = field_type.lower()
            study_field, _ = StudyField.objects.get_or_create(field_name=study_field_name)
            if set_field_type:
                study_field.field_type = field_type
            study_field.save()
            for study_id, value in df[field_name].to_dict().items():
                study, _ = Study.objects.get_or_create(study_id=study_id)
                if value is None:
                    continue
                # NOTE: StudyVariable will take care of splitting lists types.
                study_var, _ = StudyVariable.objects.get_or_create(study_field=study_field, value=str(value))
                study_var.studies.add(study)
