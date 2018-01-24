import os

from pandas import read_csv, read_excel, notnull
from django.core.management.base import BaseCommand, CommandError

from ...models import StudyField, Study, StudyVariable, EMPTY_IDENTIFIERS

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
            study_field, _ = StudyField.objects.get_or_create(field_name=field_name)
            for study_id, value in df[field_name].to_dict().items():
                study, _ = Study.objects.get_or_create(study_id=study_id)
                if value is None:
                    continue
                study_var, _ = StudyVariable.objects.get_or_create(study_field=study_field,
                                                                   value=str(value))
                study_var.studies.add(study)
                if study_field.field_type == 'list':
                    study_var.save()
